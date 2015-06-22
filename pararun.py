#!/usr/bin/env python3

'''
Run commands in parallel.

Example:

    $ pararun.py [foo] echo foo :: [bar] echo bar
    [foo] foo
    [bar] bar
'''

import argparse
from blessings import Terminal
from itertools import cycle
import subprocess
import threading
from time import sleep


t = Terminal()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    # args.command is something like ['echo', 'a', '::', 'echo', 'b']
    cmds = [[]]
    for x in args.command:
        if x == '::':
            cmds.append([])
        else:
            cmds[-1].append(x)
    # cmds is now something like [['echo', 'a'], ['echo', 'b']]
    pr = ParaRun()
    for cmd in cmds:
        if cmd[0].startswith('[') and cmd[0].endswith(']'):
            cmd, name = cmd[1:], cmd[0][1:-1]
        else:
            name = None
        pr.start(cmd, name=name)
    try:
        try:
            pr.run()
        except KeyboardInterrupt:
            print()
    finally:
        pr.close()


class ParaRun:

    def __init__(self):
        self.processes = []

    def start(self, cmd, name=None):
        assert isinstance(cmd, list)
        name = name or cmd[0]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        decoration = self.get_decoration()
        t = threading.Thread(target=self.tail, args=(p, name, decoration))
        t.start()
        self.processes.append(_Process(cmd=cmd, name=name, p=p, t=t, decoration=decoration))

    _decorations = cycle([
        t.green,
        t.blue,
        t.yellow,
        t.red,
    ])

    def get_decoration(self):
        return next(self._decorations)

    def tail(self, p, name, decoration):
        for line in p.stdout:
            print(decoration(t.bold('[' + name + ']')) + ' ' + decoration(line.rstrip()))
        p.wait()
        print('Process {name} (pid {pid}) exited with return code {rc}'.format(
            name=decoration(t.bold(name)),
            pid=p.pid, rc=p.returncode))

    def run(self):
        term = False
        while any(p.p for p in self.processes):
            for p in self.processes:
                if p.p and p.p.poll() is not None:
                    p.p = None
                    if not term and any(p.p for p in self.processes):
                        print('Terminating other processes')
                        self.terminate()
                        term = True
            sleep(.1)

    def terminate(self):
        for p in self.processes:
            if p.p:
                try:
                    p.p.terminate()
                except ProcessLookupError:
                    p.p = None

    def close(self):
        self.terminate()
        for p in self.processes:
            if p.t:
                p.t.join()
                p.t = None


class _Process:

    def __init__(self, cmd, name, p, t, decoration):
        self.cmd = cmd
        self.name = name
        self.p = p
        self.t = t
        self.decoration = decoration


if __name__ == '__main__':
    main()
