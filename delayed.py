#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
from time import sleep


def main():
    p = argparse.ArgumentParser()
    p.add_argument('delay')
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    try:
        sleep(convert_to_seconds(args.delay))
    except KeyboardInterrupt:
        print()
        sys.exit('KeyboardInterrupt while sleeping')
    try:
        subprocess.check_call(args.command)
    except subprocess.CalledProcessError as e:
        sys.exit('Command failed (return code {}): {}'.format(
            e.returncode, ' '.join(args.command)))


def convert_to_seconds(s):
    # seconds (default)
    m = re.match(r'^([0-9.]+)s?$', s)
    if m:
        return float(m.group(1))

    # minutes
    m = re.match(r'^([0-9.]+)m$', s)
    if m:
        return float(m.group(1)) * 60

    # hours
    m = re.match(r'^([0-9.]+)h$', s)
    if m:
        return float(m.group(1)) * 3600

    # days
    m = re.match(r'^([0-9.]+)d$', s)
    if m:
        return float(m.group(1)) * 24 * 3600
    raise Exception('Unknown delay format: {}'.format(s))


if __name__ == '__main__':
    main()
