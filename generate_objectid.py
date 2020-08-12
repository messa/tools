#!/usr/bin/env python3

from argparse import ArgumentParser
from bson import ObjectId
from datetime import datetime


def main():
    p = ArgumentParser()
    p.add_argument('--date', '-d')
    args = p.parse_args()
    if args.date:
        dt = datetime.strptime(args.date, '%Y-%m-%dT%H:%M:%SZ')
        oid = ObjectId.from_datetime(dt)
    else:
        oid = ObjectId()
    print(oid)


if __name__ == '__main__':
    main()
