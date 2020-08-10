#!/usr/bin/env python3

from argparse import ArgumentParser
from bson import ObjectId


def main():
    p = ArgumentParser()
    p.add_argument('objectid', nargs='+')
    args = p.parse_args()
    for oid_str in args.objectid:
        oid = ObjectId(oid_str)
        print('ObjectId:', oid, end='')
        print('  generation_time:', oid.generation_time, end='')
        print()


if __name__ == '__main__':
    main()

