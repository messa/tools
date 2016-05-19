#!/usr/bin/env python3

import argparse
import logging
import yaml
import sys

try:
    import simplejson as json
except ImportError:
    import json


logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--indent', type=int, default=4)
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    input_stream = sys.stdin
    output_stream = sys.stdout
    while True:
        line = input_stream.readline()
        if line == '':
            break
        line = line.strip()
        if line.startswith('#'):
            continue
        if not line.startswith('{'):
            logger.warning("Line doesn't start with '{': %r", line)
            continue
        if not line.endswith('}'):
            logger.warning("Line doesn't end with '}': %r", line)
            continue
        try:
            data = json.loads(line)
        except Exception as e:
            logger.exception('Failed to parse line: %r; line: %r', e, line)
        yout = yaml.dump(data, indent=args.indent, default_flow_style=False, width=120)
        output_stream.write('---\n')
        output_stream.write(yout)
    output_stream.write('...\n')


if __name__ == '__main__':
    main()
