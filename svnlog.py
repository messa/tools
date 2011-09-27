#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cStringIO import StringIO
import re
import subprocess
import sys


_headerRevisionRE = re.compile(r"^r([0-9]+) \| ")


def parse_revision_from_header(headerLine):
    m = _headerRevisionRE.match(headerLine)
    if not m:
        raise Exception("Header parse error: %r" % headerLine)
    return int(m.group(1))


def parse_svn_log_output(stream):
    separationLine = "-" * 72

    line = stream.readline()
    if not line:
        return
    if line.rstrip() != separationLine:
        raise Exception("Parse error - separation line expected instead of %r" % line)

    while True:
        headerLine = stream.readline()
        if not headerLine:
            break  # end of input

        revision = parse_revision_from_header(headerLine)

        blankLine = stream.readline()
        assert not blankLine.strip("\n")

        descriptionLines = list()

        while True:
            line = stream.readline()
            if not line:
                raise Exception("Unexpected end of input")
            if line.rstrip() == separationLine:
                break
            descriptionLines.append(line)

        description = "".join(descriptionLines)

        yield (revision, headerLine, description)


class Commands (object):

    def run_svn_log(self):
        return subprocess.Popen(
            ["svn", "log"],
            stdin=open("/dev/null"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def run_svn_diff(self, revision):
        return subprocess.Popen(
            ["svn", "diff", "-c", str(revision)],
            stdin=open("/dev/null"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def run_colordiff(self, stdin):
        return subprocess.Popen(
            ["colordiff"],
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)


def copy_output(src, dest):
    while True:
        data = src.read(8192)
        if not data:
            break
        dest.write(data)


def main(out=sys.stdout, err=sys.stderr, commands=Commands()):

    svnLogProcess = commands.run_svn_log()

    for (revision, headerLine, description) in parse_svn_log_output(svnLogProcess.stdout):

        # visual delimiter
        out.write("/" * 78 + "\n")
        out.write("/" * 78 + "\n")

        out.write(headerLine)
        out.write("\n")
        out.write(description)
        out.write("\n")

        svnDiffProcess = commands.run_svn_diff(revision)
        diffOutput = svnDiffProcess.stdout

        try:
            colordiffProcess = commands.run_colordiff(stdin=svnDiffProcess.stdout)
            diffOutput = colordiffProcess.stdout
        except OSError, e:
            # when colordiff is not found
            assert e.errno == 2  # (No such file or directory)
            colordiffProcess = None

        copy_output(diffOutput, out)

        assert svnDiffProcess.wait() == 0
        if colordiffProcess:
            assert colordiffProcess.wait() == 0

    if svnLogProcess.wait() != 0:
        svnLogErrorOutput = svnLogProcess.stderr.read()
        if svnLogErrorOutput:
            err.write(svnLogErrorOutput)
        else:
            err.write("error: svn log command exited with non-zero return code")
        sys.exit(1)


if __name__ == "__main__":
    main()


