#!/usr/bin/env python3

import argparse
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--execute', '-x', action='store_true', help='execute the rename')
    p.add_argument('pattern')
    p.add_argument('file', nargs='*')
    args = p.parse_args()

    if not args.file:
        print('No file to rename.')
        return

    for path in args.file:
        target = get_target(path, args.pattern)

        print('{} -> {}'.format(path, target))
        if Path(target).exists():
            print('  WARNING - already exists: {}'.format(target))

        if args.execute:
            Path(path).rename(target)


def get_target(path, pattern):
    return pattern.replace('@', path)


if __name__ == '__main__':
    main()
