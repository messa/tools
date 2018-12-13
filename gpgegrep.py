#!/usr/bin/env python3

from fcntl import flock, LOCK_EX
from lzma import LZMADecompressor
import os
from subprocess import Popen, DEVNULL, PIPE
import sys


lock_path = '/tmp/gpgegrep-lock-{uid}'.format(uid=os.getuid())


def main():
    _, *grep_args, filename = sys.argv
    grep_cmd = ['egrep'] + grep_args
    gpg_cmd = ['gpg2', '--decrypt', '-o', '-', filename]
    fl = open(lock_path, 'wb')
    flock(fl, LOCK_EX)
    grep_process = None
    gpg_process = None
    try:
        grep_process = Popen(grep_cmd, stdin=PIPE)
        gpg_process = Popen(gpg_cmd, stdin=DEVNULL, stdout=PIPE, stderr=DEVNULL)
        head = b''
        while True:
            if grep_process.returncode is not None:
                sys.exit('grep command has failed with returncode {}'.format(grep_process.returncode))
            if gpg_process.returncode is not None:
                sys.exit('GPG command has failed with returncode {}'.format(gpg_process.returncode))
            buf = gpg_process.stdout.read(65536)
            if buf == b'':
                if head == b'':
                    sys.exit('Nothing received from gpg')
                break
            if fl is not None:
                fl.close()
                fl = None
            if head is not None:
                head += buf
                if len(head) < 100:
                    continue
                else:
                    if head.startswith(b'\xFD7zXZ\x00\x00'):
                        decompressor = LZMADecompressor()
                    else:
                        decompressor = None
                    buf = head
                    head = None
            if decompressor is not None:
                buf = decompressor.decompress(buf)
                if decompressor.eof:
                    assert not decompressor.unused_data
            try:
                grep_process.stdin.write(buf)
            except BrokenPipeError:
                sys.exit(1)
        gpg_process.wait()
        grep_process.stdin.close()
        grep_process.wait()
        grep_process = None
    finally:
        if gpg_process:
            gpg_process.terminate()
        if grep_process:
            grep_process.terminate()
        if gpg_process:
            gpg_process.wait()
        if grep_process:
            grep_process.wait()


if __name__ == '__main__':
    main()
