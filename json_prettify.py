#!/usr/bin/env python

import json
import sys


def main():
    data = json.load(sys.stdin)
    json.dump(data, sys.stdout, indent=4)
    print ""


if __name__ == "__main__":
    main()

