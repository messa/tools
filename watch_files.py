#!/usr/bin/env python3

'''
Watch files/directories for any changes and execute given command.

Alternatives:

- entr - http://eradman.com/entrproject/
- watchdog - https://github.com/gorakhargosh/watchdog
'''

import argparse
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import threading
from time import sleep

try:
    from colorama import Style
    C_DIM = Style.DIM
    C_RESET = Style.RESET_ALL
except ImportError:
    C_DIM = ''
    C_RESET = ''


skip_names = set('''
    site-packages
    python-wheels
    __pycache__
    local
'''.split())


skip_suffixes = '''
    .lock
    .log
    .pyc
    .wt
    .egg-info
'''.split()


class SkipPolicy:

    def skip_directory(self, path):
        if path.name.startswith('.'):
            return True
        if path.name in skip_names:
            return True
        if any(path.name.endswith(s) for s in skip_suffixes):
            return True
        return False


stop_event = threading.Event()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', '-p', metavar='PATH', action='append', help='directory/file to watch')
    p.add_argument('--terminate', '-t', action='store_true')
    p.add_argument('--interval', '-i', type=float, default=.25)
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()

    watch_paths = args.path or ['.']
    watch_paths = [Path(p) for p in watch_paths]

    setup_signals()

    if args.terminate:
        run_terminate(watch_paths, args.interval, args.command)
    else:
        run_wait(watch_paths, args.interval, args.command)


def run_terminate(watch_paths, interval, command):
    '''
    Run the command at the beginning and when any files change.
    If the command is already running then terminate it and run again.
    '''
    p = None
    state = None
    try:
        while True:
            if stop_event.is_set():
                print('Stopped')
                return
            current_state = scan_state(watch_paths)
            if current_state == state:
                stop_event.wait(interval)
            else:
                if p:
                    try:
                        os.killpg(p.pid, signal.SIGTERM)
                    except Exception as e:
                        print('Failed to killpg({pid}): {e}'.format(pid=p.pid, e=e), file=sys.stderr)
                    p.wait()
                    stop_event.wait(.1)
                if stop_event.is_set():
                    return
                print_changed_files(state, current_state)
                state = current_state
                p = subprocess.Popen(command, start_new_session=True)
    finally:
        if p:
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except Exception as e:
                print('Failed to killpg({pid}): {e}'.format(pid=p.pid, e=e), file=sys.stderr)
            p.wait()


def run_wait(watch_paths, interval, command):
    '''
    Run the command at the beginning and when any files change.
    If the command is already running then wait for it to finish before running again.
    '''
    state = None
    while True:
        if stop_event.is_set():
            print('Stopped')
            return
        current_state = scan_state(watch_paths)
        if current_state == state:
            stop_event.wait(interval)
        else:
            print_changed_files(state, current_state)
            state = current_state
            rc = subprocess.call(command)
            if rc != 0:
                print('Return code: {}'.format(rc), file=sys.stderr, flush=True)


def setup_signals():
    def handler(signum, frame):
        stop_event.set()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def print_changed_files(old_state, new_state):
    if not old_state:
        return
    pr = lambda s: print(C_DIM + s + C_RESET, file=sys.stderr, flush=True)
    pr('_' * 80)
    pr('')
    pr('Changed files:')
    all_keys = old_state.keys() | new_state.keys()
    for k in sorted(all_keys):
        if old_state.get(k) != new_state.get(k):
            pr('  - {}'.format(k))
    pr('_' * 80)
    pr('')


def scan_state(paths):
    scanner = StatStateScanner(skip_policy=SkipPolicy())
    return scanner.scan(paths)


class StatStateScanner:

    def __init__(self, skip_policy):
        self.skip_policy = skip_policy

    def scan(self, paths):
        state = {}
        for p in paths:
            assert isinstance(p, Path)
            self._scan_path(state, p)
        return state

    def _scan_path(self, state, p):
        st = p.stat()
        if stat.S_ISDIR(st.st_mode):
            self._scan_dir(state, p)
        elif stat.S_ISREG(st.st_mode):
            self._scan_file(state, p, st)

    def _scan_dir(self, state, p):
        for ip in p.iterdir():
            if self.skip_policy.skip_directory(ip):
                continue
            self._scan_path(state, ip)

    def _scan_file(self, state, p, st):
        state[str(p)] = (st.st_size, st.st_mtime)


if __name__ == '__main__':
    main()
