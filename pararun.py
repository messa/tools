#!/usr/bin/env python

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

Processes are terminated when the first one finishes. To avoid this, use
parameter --wait:

    $ ./pararun.py --wait large_batch :: small_batch
'''

import argparse
from blessings import Terminal
from itertools import cycle
import subprocess
import sys
import threading
from time import sleep


if sys.version < '3.':
    # uf...
    reload(sys)
    sys.setdefaultencoding("utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--color', '-c', action='store_true', help='force color output')
    p.add_argument('--wait', '-w', action='store_true', help='do not terminate processes, wait for the last one to finish')
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
    try:
        pr = ParaRun(term)
        for cmd in cmds:
            if cmd[0].startswith('[') and cmd[0].endswith(']'):
                name, cmd = cmd[0], cmd[1:]
                name = name[1:-1] # strip '[' and ']'
            else:
                name = None
            pr.start(cmd, name=name)
        try:
            try:
                if args.wait:
                    pr.run_until_last_one_finishes()
                else:
                    pr.run_until_first_one_finishes()
            except KeyboardInterrupt:
                print()
        finally:
            pr.close()
    except AppError as e:
        sys.exit('ERROR: {}'.format(e))


class AppError (Exception):
    pass


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
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
        except Exception as e:
            raise AppError('Failed to start command {}: {}'.format(cmd, e))
        decoration = self.get_decoration()
        #print('Process {name} started (pid {pid})'.format(
        #    name=decoration(self.term.bold(name)), pid=process.pid))
        tail_thread = threading.Thread(target=self.tail, args=(process, name, decoration))
        tail_thread.start()
        self.processes.append(_ProcessInfo(
            cmd=cmd, name=name, process=process,
            tail_thread=tail_thread, decoration=decoration))

    def get_decoration(self):
        return next(self.decorations)

    def tail(self, process, name, decoration):
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(decoration(self.term.bold('[' + name + ']')) + ' ' + decoration(line.rstrip()))
            sys.stdout.flush()
        process.wait()
        print('Process {name} (pid {pid}) exited with return code {rc}'.format(
            name=decoration(self.term.bold(name)),
            pid=process.pid, rc=process.returncode))

    def run_until_first_one_finishes(self):
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

    def run_until_last_one_finishes(self):
        while any(pi.process for pi in self.processes):
            for pi in self.processes:
                if pi.process and pi.process.poll() is not None:
                    pi.process = None
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
