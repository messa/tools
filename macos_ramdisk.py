#!/usr/bin/env python3

'''
You can add this fragment to your ~/.bash_profile to setup TMPDIR env.
variable automatically:

    if [ -d /Volumes/ramdisk/tmp ]; then
      export TMPDIR=/Volumes/ramdisk/tmp
    fi
'''

import argparse
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


class AppError (Exception):
    pass


def parse_size(s):
    '''
    Velikost zadanou v jakýchkoliv obvyklých jednotkách vrací v bajtech.
    '''
    assert isinstance(s, str)
    m = re.match(r'^([0-9]+) *([^0-9]*)$', s)
    if not m:
        raise AppError('Failed to parse size {!r}'.format(s))
    n = int(m.group(1))
    unit = m.group(2)
    if not unit:
        return n
    if unit.lower() in ('k', 'kb'):
        return n * 2**10
    if unit.lower() in ('m', 'mb'):
        return n * 2**20
    if unit.lower() in ('g', 'gb'):
        return n * 2**30
    raise AppError('Unknown unit {}'.format(unit))


assert parse_size("1k") == 2**10
assert parse_size("1K") == 2**10
assert parse_size("1kB") == 2**10
assert parse_size("1KB") == 2**10
assert parse_size("1m") == 2**20
assert parse_size("1M") == 2**20
assert parse_size("1MB") == 2**20
assert parse_size("1g") == 2**30
assert parse_size("1G") == 2**30
assert parse_size("1GB") == 2**30


def main():
    if sys.platform != 'darwin':
        sys.exit(
            'This script is designed for darwin (macOS); '
            'you are using {}'.format(sys.platform))

    p = argparse.ArgumentParser()
    p.add_argument('--mountpoint', default='/Volumes/ramdisk')
    p.add_argument('--size', default='600M')
    args = p.parse_args()

    mountpoint = Path(args.mountpoint)
    size = parse_size(args.size)
    if not mountpoint.is_dir():
        create_directory(mountpoint)
    mountpoint = mountpoint.resolve()
    if list(mountpoint.iterdir()):
        raise AppError('Mountpoint directory {} is not empty'.format(mountpoint))
    if already_mounted(mountpoint):
        raise AppError('Some filesystem is already mounted at {}'.format(mountpoint))
    device_name = create_ramdisk_device(size)
    create_filesystem(device_name)
    mount(device_name, mountpoint)
    (mountpoint / 'tmp').mkdir()
    (mountpoint / 'tmp').chmod(0o777 | stat.S_ISVTX)
    print('Done.')
    print()
    print('If you want to use the ramdisk as TMPDIR, run these commands:')
    print()
    print('TMPDIR={}; export TMPDIR'.format(mountpoint / 'tmp'))
    tmpdir = os.getenv('TMPDIR')
    if tmpdir:
        print()
        print('(Current TMPDIR is {})'.format(tmpdir))


def create_directory(path):
    print('Creating directory {}'.format(path))
    path.mkdir()


def already_mounted(mountpoint):
    output = check_output(['mount'])
    for n, line in enumerate(output.decode().splitlines()):
        m = re.match(r'^(.*) on (/.*) (\(.*\))$', line)
        if not m:
            raise AppError('Failed to parse line {} of output of the command mount: {}'.format(n, line))
        location = m.group(2)
        if location == str(mountpoint):
            return True
    return False


def create_ramdisk_device(size):
    assert isinstance(size, int)
    print('Creating ramdisk device with size {:.2f} MB'.format(size / 2**20))
    sectors = size / 512
    output = check_output(
        ['hdiutil', 'attach', '-nomount', 'ram://{}'.format(sectors)])
    output = output.decode().strip()
    if not re.match(r'^/dev/disk[0-9]+$', output):
        raise Exception('Invalid hdiutil output: {!r}'.format(output))
    print('Created device {}'.format(output))
    return output


def create_filesystem(device_name):
    print('Checking whether {} contains no data'.format(device_name))
    with open(device_name, 'rb') as f:
        block = f.read(4096)
        assert block == b'\0' * len(block)
    print('Creating HFS filesystem on {}'.format(device_name))
    check_output(['newfs_hfs', device_name])


def mount(device_name, mountpoint):
    print('Mounting {} on {}'.format(device_name, mountpoint))
    check_output(
        ['mount', '-o', 'noatime', '-t', 'hfs', device_name, str(mountpoint)])


def check_output(cmd):
    print('>', ' '.join(cmd))
    return subprocess.check_output(cmd)


if __name__ == '__main__':
    try:
        main()
    except AppError as e:
        sys.exit('Error: {}'.format(e))
