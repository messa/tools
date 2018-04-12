#!/usr/bin/env python3

import argparse
import csv
import json
import logging
import os
import reprlib
import sys


logger = logging.getLogger(__name__)


_repr_obj = reprlib.Repr()
_repr_obj.maxstring = 200
_repr_obj.maxother = 200
smart_repr = _repr_obj.repr



def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v', action='store_true')
    p.add_argument('--yaml', action='store_true')
    p.add_argument('csv_file', nargs='?')
    args = p.parse_args()

    logging.basicConfig(
        format='%(levelname)5s: %(message)s',
        level=logging.DEBUG if args.verbose else logging.WARNING)

    if not args.csv_file or args.csv_file == '-':
        csv_data = sys.stdin.buffer.read()
    else:
        csv_data = open(args.csv_file, 'rb').read()

    try:
        csv_to_jsonl(csv_data, yaml_output=args.yaml)
    except BrokenPipeError as e:
        os._exit(1)


def csv_to_jsonl(csv_data, yaml_output):
    assert isinstance(csv_data, bytes)
    logger.debug('data: %s', smart_repr(csv_data))
    text = decode(csv_data)
    logger.debug('decoded: %s', smart_repr(text))

    dialect = csv.Sniffer().sniff(text[:100000])
    logger.debug('Sniffed CSV dialect: %s', obj_attributes(dialect))

    lines = text.splitlines(True)
    reader = csv.DictReader(lines, dialect=dialect)
    rows = list(reader)
    logger.debug('Total CSV rows: %s', len(rows))

    for row in rows:
        if '' in row and row[''] == None or row[''] == '':
            row.pop('')

    if yaml_output:
        import yaml
        for row in rows:
            if row.get('') == '':
                del row['']
            print(yaml.dump(dict(row), default_flow_style=False, width=250, allow_unicode=True).rstrip('\n'))
            print('---')
    else:
        for row in rows:
            print(json.dumps(row))


def obj_attributes(obj):
    attrs = {}
    for k in dir(obj):
        if k.startswith('_'):
            continue
        v = getattr(obj, k)
        if callable(v):
            continue
        attrs[k] = v
    return attrs


def decode(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as e:
        logger.info('Failed to decode as UTF-8: %s', smart_repr(e))
    return data.decode('cp1250')


if __name__ == '__main__':
    main()
