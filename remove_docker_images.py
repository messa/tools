#!/usr/bin/env python3

import argparse
import re
import subprocess


keep_tags = '''
    latest
    production
    testing
    jessie
    '''.split()


def main():
    p = argparse.ArgumentParser()
    args = p.parse_args()
    img_out = subprocess.check_output(['docker', 'images'], universal_newlines=True)
    img_lines = img_out.splitlines()
    img_header, *img_list = img_lines

    assert re.match(r'^REPOSITORY +TAG +IMAGE ID +.*', img_header)
    for line in img_list:
        parts = line.split()
        repo, tag, img_id, *_ = parts
        if tag in keep_tags:
            continue
        cmd = ['docker', 'rmi', img_id]
        print('Calling {}'.format(' '.join(cmd)))
        try:
            subprocess.check_call(cmd, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            print(e)


if __name__ == '__main__':
    main()
