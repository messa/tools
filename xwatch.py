#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run one command repeatedly, separate outputs with blank lines.

This is an alternative to the 'watch' command, but the fullscreen-like
behavior is done with blank lines, so the output can be easily scrolled.
"""

__author__ = "Petr Messner"


import os
import sys
import optparse
import subprocess
import time


class Stopwatch (object):

    def __init__(self):
        self.startTime = None
        self.stopTime = None

    def start(self):
        self.startTime = time.time()
        self.stopTime = None

    def stop(self):
        self.stopTime = time.time()

    @property
    def duration(self):
        assert self.stopTime is not None
        return self.stopTime - self.startTime



def _get_output(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE)
    (stdout, _) = p.communicate()
    assert p.wait() == 0
    return stdout



class Terminal (object):

    def get_height(self):
        return int(_get_output(["tput", "lines"]).strip())

    def gray(self):
        subprocess.check_call(["tput", "setaf", "8"])

    def reset_colors(self):
        subprocess.check_call(["tput", "op"])


def getTime():
    return time.strftime("%H:%M:%S")


class XWatch (object):

    def __init__(self, terminal=Terminal(), stopwatch=Stopwatch(),
                 stdout=sys.stdout, getTime=getTime):
        self.terminal = terminal
        self.stdout = stdout
        self.stopwatch = stopwatch
        self.getTime = getTime
        self.interval = 1.0
        self.command = None


    def run_loop(self):
        while True:
            self.run_one()
            time.sleep(self.interval)


    def run_command(self):
        assert self.command
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True)
        output = p.stdout.read()
        p.wait()
        return output


    def run_one(self):
        self.stopwatch.start()
        output = self.run_command()
        self.stopwatch.stop()

        if not output.endswith("\n"):
            output += "\n"

        lineCount = len(output.splitlines())
        terminalLines = self.terminal.get_height()
        neededSpace = terminalLines - lineCount - 2
        if neededSpace > 0:
            self.stdout.write("\n" * neededSpace)
        else:
            # let the output be divided by at least one blank line
            self.stdout.write("\n")

        self.stdout.write(output)
        self.stdout.flush()

        self.write_footer(duration=self.stopwatch.duration)


    def write_footer(self, duration):
        self.terminal.gray()
        self.stdout.write(
            "%s  %s  %.3f s" % (self.command, self.getTime(), duration))
        self.stdout.flush()
        self.terminal.reset_colors()
        self.stdout.write("\n")



def main():
    op = optparse.OptionParser()
    (options, args) = op.parse_args()

    w = XWatch()

    if not args:
        sys.stderr.write("No arguments provided; nothing to run.\n")
        sys.exit(1)

    w.command = " ".join(args)

    w.run_loop()



if __name__ == "__main__":
    main()


