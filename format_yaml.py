#!/usr/bin/env python3

import argparse
import yaml


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in-place', '-i', action='store_true')
    p.add_argument('input_file')
    args = p.parse_args()
    original = open(args.input_file).read()
    data = yaml.load(original)
    formatted = yaml.dump(data, default_flow_style=False)
    if args.in_place:
        if original != formatted:
            with open(args.input_file, 'w') as f:
                f.write(formatted)
    else:
        print(formatted.rstrip())


if __name__ == '__main__':
    main()

