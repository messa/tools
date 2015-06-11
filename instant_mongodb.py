#!/usr/bin/env python

import logging
import optparse
import os
from os.path import isdir
import subprocess


localhost = "127.0.0.1"
logger = logging.getLogger("instant_mongodb")


def main():
    op = optparse.OptionParser()
    op.add_option("--datadir", "-d", default="mongo-data")
    op.add_option("--port", "-p", default="7017")
    op.add_option("--verbose", "-v", default=False, action="store_true")
    op.add_option("--auth", "-a", default=False, action="store_true", help="run with security")
    options, args = op.parse_args()

    setup_logging(verbose=options.verbose)

    p = mongodb_process(data_dir=options.datadir, port=int(options.port), auth=options.auth)
    p.wait()


def setup_logging(verbose):
    r = logging.getLogger("")
    r.addHandler(logging.StreamHandler())
    r.setLevel(logging.DEBUG if verbose else logging.INFO)


def mongodb_process(data_dir, port, auth):
    if not isdir(data_dir):
        os.mkdir(data_dir)
    cmd = [
        "mongod",
        "--port", str(port),
        "--bind_ip", localhost,
        "--nounixsocket",
        "--dbpath", data_dir,
        "--smallfiles"]
    if auth:
        cmd.append("--auth")
    p = subprocess.Popen(cmd)
    return p


if __name__ == "__main__":
    main()

