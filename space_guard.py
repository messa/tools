#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

try:
    import psutil
except ImportError:
    psutil = None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', '-p', metavar='PATH', action='append', help='mountpoint to watch')
    p.add_argument('--interval', '-i', type=float, default=1)
    p.add_argument('--min', '-m', type=float, default=2, help='minimum free space in GB')
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    checked_paths = args.path or ['.']
    low = check_free_space(args.min, checked_paths)
    if low:
        print('Low disk space:', low, file=sys.stderr)
        sys.exit(1)
    p = subprocess.Popen(args.command)
    while True:
        try:
            p.wait(args.interval)
        except subprocess.TimeoutExpired:
            pass
        else:
            sys.exit(p.returncode)
        low = check_free_space(args.min, checked_paths)
        if low:
            print('Low disk space:', low, file=sys.stderr)
            p.terminate()
            p.wait()
            sys.exit(1)


def check_free_space(min_gb, paths):
    low = []
    for p in paths:
        free_gb = get_free_space(p) / 2**30
        if free_gb < min_gb:
            low.append('{} ({:.2f} GB)'.format(p, free_gb))
    return ', '.join(low)


def get_free_space(path):
    if psutil:
        return psutil.disk_usage(path).free
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


if __name__ == '__main__':
    main()
