#!/usr/bin/env python3

import argparse
import logging
import optparse
import os
from os.path import isdir
import subprocess


localhost = '127.0.0.1'
logger = logging.getLogger('instant_mongodb' if __name__ == '__main__' else __name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--datadir', '-d', default='mongo-data')
    p.add_argument('--port', '-p', default='7017')
    p.add_argument('--verbose', '-v', action='store_true')
    p.add_argument('--auth', '-a', action='store_true', help='run with security')
    p.add_argument('--wiredTiger', '-w', action='store_true')
    args = p.parse_args()

    setup_logging(verbose=args.verbose)

    p = mongodb_process(
        data_dir=args.datadir, port=int(args.port),
        auth=args.auth, wiredtiger=args.wiredTiger)
    p.wait()


def setup_logging(verbose):
    r = logging.getLogger('')
    r.addHandler(logging.StreamHandler())
    r.setLevel(logging.DEBUG if verbose else logging.INFO)


def mongodb_process(data_dir, port, auth, wiredtiger):
    if not isdir(data_dir):
        os.mkdir(data_dir)
    cmd = [
        'mongod',
        '--port', str(port),
        '--bind_ip', localhost,
        '--nounixsocket',
        '--dbpath', data_dir,
        '--smallfiles']
    if auth:
        cmd.append('--auth')
    if wiredtiger:
        cmd.extend(['--storageEngine', 'wiredTiger'])
        cmd.extend(['--wiredTigerCacheSizeGB', '1'])
    p = subprocess.Popen(cmd)
    return p


if __name__ == '__main__':
    main()

