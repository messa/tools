#!/usr/bin/env python3

import argparse
import json
import os
import sys


def main():
    p = argparse.ArgumentParser()
    args = p.parse_args()
    for line in sys.stdin:
        row = json.loads(line)
        try:
            print(json.dumps(row, sort_keys=True))
        except BrokenPipeError as e:
            os._exit(1)


if __name__ == '__main__':
    main()
