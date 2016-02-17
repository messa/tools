#!/usr/bin/env python3

import re
import subprocess


def main():
    img_out = subprocess.check_output(['docker', 'images'], universal_newlines=True)
    img_lines = img_out.splitlines()
    img_header, img_list = img_lines[0], img_lines[1:]
    assert re.match(r'^REPOSITORY +TAG +IMAGE ID +.*', img_header)
    for img in img_list:
        m = re.match(r'([a-zA-Z0-9<>.-]+) +([a-zA-Z0-9<>.-]+) +([0-9a-f]+) +.*', img)
        assert m, repr(img)
        img_repo, img_tag, img_id = m.group(1), m.group(2), m.group(3)
        cmd = ['docker', 'rmi', img_id]
        print('Calling {}...'.format(' '.join(cmd)))
        subprocess.check_call(cmd, universal_newlines=True)


if __name__ == '__main__':
    main()

