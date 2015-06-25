#!/usr/bin/env python3

'''
Run commands in parallel.

Example:

    $ ./pararun.py echo foo
    [echo] foo

Commands are separated by `::`:

    $ ./pararun.py echo foo :: echo bar
    [echo] foo
    [echo] bar

Commands can be labelled by adding "[name]" before a command:

    $ ./pararun.py [foo] echo foo :: [bar] echo bar
    [foo] foo
    [bar] bar

More real-world example:

    $ ./pararun.py instant_mongodb.py :: gulp watch :: ./web_app.py
'''

import argparse
from blessings import Terminal
from itertools import cycle
import subprocess
import threading
from time import sleep


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--color', '-c', action='store_true', help='force color output')
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    term = Terminal(force_styling=args.color)
    # args.command is something like ['echo', 'a', '::', 'echo', 'b']
    cmds = [[]]
    for x in args.command:
        if x == '::':
            cmds.append([])
        else:
            cmds[-1].append(x)
    # cmds is now something like [['echo', 'a'], ['echo', 'b']]
    pr = ParaRun(term)
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

    def __init__(self, term):
        self.term = term
        self.processes = []
        self.decorations = cycle([
            self.term.green,
            self.term.blue,
            self.term.yellow,
            self.term.magenta,
            self.term.cyan,
            self.term.red,
        ])

    def start(self, cmd, name=None):
        assert isinstance(cmd, list)
        name = name or cmd[0]
        process = subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            universal_newlines=True)
        decoration = self.get_decoration()
        tail_thread = threading.Thread(target=self.tail, args=(process, name, decoration))
        tail_thread.start()
        self.processes.append(_ProcessInfo(
            cmd=cmd, name=name, process=process,
            tail_thread=tail_thread, decoration=decoration))

    def get_decoration(self):
        return next(self.decorations)

    def tail(self, process, name, decoration):
        for line in process.stdout:
            print(decoration(self.term.bold('[' + name + ']')) + ' ' + decoration(line.rstrip()))
        process.wait()
        print('Process {name} (pid {pid}) exited with return code {rc}'.format(
            name=decoration(self.term.bold(name)),
            pid=process.pid, rc=process.returncode))

    def run(self):
        stop = False
        while any(pi.process for pi in self.processes):
            for pi in self.processes:
                if pi.process and pi.process.poll() is not None:
                    pi.process = None
                    if not stop and any(pi2.process for pi2 in self.processes):
                        print('Terminating other processes')
                        self.terminate()
                        stop = True
            sleep(0.1)

    def terminate(self):
        for pi in self.processes:
            if pi.process:
                try:
                    pi.process.terminate()
                except ProcessLookupError:
                    pi.process = None

    def close(self):
        self.terminate()
        for pi in self.processes:
            if pi.tail_thread:
                pi.tail_thread.join()
                pi.tail_thread = None


class _ProcessInfo:

    def __init__(self, cmd, name, process, tail_thread, decoration):
        self.cmd = cmd
        self.name = name
        self.process = process
        self.tail_thread = tail_thread
        self.decoration = decoration


if __name__ == '__main__':
    main()
