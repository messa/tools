#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Trim excessive whitespace from line ends in text files.
"""

__author__ = "Petr Messner"


import optparse
import os
import re
import stat
import sys
from os.path import join as path_join


SKIPPED_EXTENSIONS = (
    ".class",
    ".gif",
    ".gz",
    ".jar",
    ".jpeg",
    ".jpg",
    ".png",
    ".psd",
    ".pyc",
    ".tar",
    ".zip",
)

MAX_TRIM_FILE_SIZE = 512000


class StatResult (object):
    """
    Result from FS stat method.
    """

    def __init__(self, size=None, isDir=False, isFile=False):
        self.isDir = isDir
        self.isFile =isFile
        self.size = size

    def __str__(self):
        return "<%s isDir=%r isFile=%r size=%r>" % (
            self.__class__.__name__, self.isDir, self.isFile, self.size)


class FS (object):
    """
    Filesystem abstraction; can be replaced with mock object in tests.
    """

    def listdir(self, path):
        return os.listdir(path)

    def stat(self, path):
        s = os.stat(path)
        return StatResult(
            size=s.st_size,
            isDir=stat.S_ISDIR(s.st_mode),
            isFile=stat.S_ISREG(s.st_mode))

    def get_contents(self, path):
        f = open(path, "rb")
        data = f.read()
        f.close()
        return data

    def write(self, path, data):
        f = open(path, "wb")
        f.write(data)
        f.close()


def trim_line(line):
    """
    Remove ending whitespace from line.
    """
    n = len(line)
    lineEnding = ""
    while n > 0:
        n -= 1
        if line[n] in ("\r", "\n"):
            lineEnding = line[n] + lineEnding
        elif line[n] not in (" ", "\t"):
            n += 1
            break

    return line[:n] + lineEnding


class Trim (object):

    def __init__(self, fs, stdout, dryRun=False):
        self.fs = fs
        self.stdout = stdout
        self.dryRun = bool(dryRun)

    def process(self, path, skipLargeSize=False):
        st = self.fs.stat(path)
        if st.isDir:
            self.process_dir(path)
        elif st.isFile:
            if st.size < MAX_TRIM_FILE_SIZE or not skipLargeSize:
                self.process_file(path)


    def process_dir(self, path):
        names = self.fs.listdir(path)
        for name in sorted(names):
            if name.startswith(".") or name.endswith("~"):
                continue
            if any(name.endswith(ext) for ext in SKIPPED_EXTENSIONS):
                continue

            p = path_join(path, name)
            self.process(p, skipLargeSize=True)


    def process_file(self, path):
        data = self.fs.get_contents(path)
        trimmedData = "".join(trim_line(line) for line in data.splitlines(True))
        if trimmedData != data:
            self.stdout.write(path + "\n")
            if not self.dryRun:
                self.fs.write(path, trimmedData)


def main(fs=FS(), stdout=sys.stdout):
    op = optparse.OptionParser()
    op.add_option(
        "--dry-run", "-n",
        dest="dryRun", default=False,
        action="store_true")
    (options, args) = op.parse_args()

    t = Trim(fs=fs, stdout=stdout, dryRun=options.dryRun)
    if args:
        for arg in args:
            t.process(arg)
    else:
        t.process(".")


if __name__ == "__main__":
    main()

