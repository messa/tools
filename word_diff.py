#!/usr/bin/env python3

import argparse
import blessings
import difflib
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('file1')
    p.add_argument('file2')
    args = p.parse_args()
    WordDiff().diff_files(args.file1, args.file2)


class WordDiff:

    def __init__(self):
        self.t = blessings.Terminal(force_styling=True)

    def diff_files(self, f1_path, f2_path):
        a = open(f1_path).read()
        b = open(f2_path).read()
        a, b = self.preprocess(a), self.preprocess(b)
        assert isinstance(a, str)
        assert isinstance(b, str)
        ops = difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
        out = sys.stdout.write
        removed = self.t.red_bold
        inserted = self.t.green_bold
        for tag, i1, i2, j1, j2 in ops:
            if tag == 'replace':
                out(removed(a[i1:i2]))
                out(inserted(b[j1:j2]))
            elif tag == 'delete':
                assert j1 == j2
                out(removed(a[i1:i2]))
            elif tag == 'insert':
                assert i1 == i2
                out(inserted(b[j1:j2]))
            elif tag == 'equal':
                assert i2 - i1 == j2 - j1
                assert a[i1:i2] == b[j1:j2]
                out(a[i1:i2])
            else:
                assert 0, tag

    def preprocess(self, s):
        s = s.replace('\t', '\\t')
        s = s.replace(' ', '·')
        return s


if __name__ == '__main__':
    main()
