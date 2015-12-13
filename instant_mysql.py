#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import threading


logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bootstrap', '-b', action='store_true')
    p.add_argument('--clean', '-c', action='store_true', help='remove env before bootstrap')
    p.add_argument('--port', type=int, default=3306)
    p.add_argument('--env', '-e', default='mysql-env')
    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)5s: %(message)s' if args.verbose else '%(message)s')
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit())
    # ^^^ sys.exit() will raise SystemExit and all finally and catch blocks
    #     will be executed, terminating any running subprocesses
    try:
        im = InstantMySQL(env_dir=args.env, port=args.port)
        if args.bootstrap:
            if args.clean:
                im.remove_env()
            im.bootstrap()
        else:
            try:
                im.run()
            except KeyboardInterrupt:
                # do not print stack trace for ctrl-c
                pass
    except UserError as e:
        sys.exit('ERROR: {}'.format(e))


class UserError (Exception):
    pass


class InstantMySQL (object):

    def __init__(self, env_dir, port):
        self.logger = logger
        self.env_dir = Path(env_dir)
        self.port = port

    data_dir     = property(lambda self: self.env_dir / 'data')
    socket_path  = property(lambda self: self.env_dir / 'mysqld.sock')
    pidfile_path = property(lambda self: self.env_dir / 'mysqld.pid')


    def find_mysqld(self):
        '''
        Finds where is mysqld executable and its auxiliary files located on filesystem.

        Currently supports OS X + MacPorts and Debian.
        '''
        if Path('/opt/local/lib/mysql56/bin/mysqld').is_file():
            # OS X + MacPorts
            self.mysqld_path    = Path('/opt/local/lib/mysql56/bin/mysqld')
            self.mysqld_basedir = Path('/opt/local')
            self.mysqld_pkgdir  = Path('/opt/local/share/mysql56')
        elif Path('/opt/local/lib/mysql55/bin/mysqld').is_file():
            # OS X + MacPorts
            self.mysqld_path    = Path('/opt/local/lib/mysql55/bin/mysqld')
            self.mysqld_basedir = Path('/opt/local')
            self.mysqld_pkgdir  = Path('/opt/local/share/mysql55')
        elif Path('/usr/sbin/mysqld').is_file():
            # Debian etc.
            self.mysqld_path    = Path('/usr/sbin/mysqld')
            self.mysqld_basedir = Path('/usr')
            self.mysqld_pkgdir  = Path('/usr/share/mysql')
        else:
            raise Exception('Could not find MySQL server files')
        assert self.mysqld_path.is_file()
        assert self.mysqld_basedir.is_dir()
        assert self.mysqld_pkgdir.is_dir()


    def run(self):
        '''
        Run mysqld.

        It is expected that the datadir is already prepared using bootstrap.
        '''
        self.find_mysqld()
        if not self.env_dir.is_dir():
            raise UserError('Env dir {} does not exist; run with --bootstrap first'.format(self.env_dir))
        self.env_dir = self.env_dir.resolve()
        assert self.data_dir.is_dir(), self.data_dir
        cmd = [
            str(self.mysqld_path),
            '--basedir={}'.format(self.mysqld_basedir),
            '--datadir={}'.format(self.data_dir),
            '--socket={}'.format(self.socket_path),
            '--port={}'.format(self.port),
            '--pid-file={}'.format(self.pidfile_path),
            '--skip-networking=off',
            '--bind-address=127.0.0.1',
            '--innodb-file-per-table',
            '--innodb-flush-log-at-trx-commit=0',
        ]
        self.logger.info('Running %s', ' '.join(cmd))
        p = subprocess.Popen(cmd)
        try:
            try:
                try:
                    rc = p.wait()
                    raise UserError('Process {} exited with return code {}'.format(cmd[0], rc))
                except KeyboardInterrupt:
                    print()
            finally:
                self.terminate(p, name=cmd[0])
        finally:
            # in some scenarios two signals (SIGINT and SIGTERM) are received,
            # so this finally block is doubled to be sure to really terminate mysqld
            self.terminate(p, name=cmd[0])


    def remove_env(self):
        '''
        Remove env dir with all its contents.
        '''
        if self.env_dir.is_dir():
            self.logger.info('Removing %s', self.env_dir)
            shutil.rmtree(str(self.env_dir))


    def bootstrap(self):
        '''
        Create env dir, data dir, run mysqld --bootstrap and pass it scripts
        to create system tables.
        '''
        self.find_mysqld()
        if self.env_dir.is_dir():
            raise UserError('Env dir {} already exists, cannot bootstrap'.format(self.env_dir))
        self.env_dir.mkdir()
        try:
            self.env_dir = self.env_dir.resolve()
            self.data_dir.mkdir()
            (self.data_dir / 'mysql').mkdir()
            (self.data_dir / 'test').mkdir()
            cmd = [
                str(self.mysqld_path),
                "--bootstrap",
                "--basedir={}".format(self.mysqld_basedir),
                "--datadir={}".format(self.data_dir),
                "--max_allowed_packet=8M",
                "--default-storage-engine=myisam", # maybe InnoDB would be better?
                "--net_buffer_length=16K"
            ]
            self.logger.info('Running %s', ' '.join(cmd))
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)
            self.tail(p.stdout, 'stdout: ')
            self.tail(p.stderr, 'stderr: ')
            try:
                try:
                    try:
                        self.feed_bootstrap_scripts(p.stdin)
                    except KeyboardInterrupt:
                        print()
                        # this may take a while, so we write message that we are stopping
                        print('Interrupting...')
                        raise
                finally:
                    p.stdin.close()
                rc = p.wait()
                if rc != 0:
                    raise UserError('Process {} exited with return code {}'.format(cmd[0], rc))
                self.logger.info('Process %s finished', cmd[0])

            finally:
                self.terminate(p, name=cmd[0])
        except:
            self.logger.warning(
                'Bootstrap did not finish successfully; '
                'directory %s should be removed (use --bootstrap --clean)',
                self.env_dir)
            raise


    def feed_bootstrap_scripts(self, stdin):
        '''
        Helper method for bootstrap()
        '''
        def wr(line):
            self.logger.debug('stdin: %s', line.rstrip())
            stdin.write(line)
            stdin.flush()
        wr('use mysql;\n')
        self.logger.info('Processing mysql_system_tables.sql')
        for line in (self.mysqld_pkgdir / 'mysql_system_tables.sql').open():
            wr(line)
        self.logger.info('Processing mysql_system_tables_data.sql')
        for line in (self.mysqld_pkgdir / 'mysql_system_tables_data.sql').open():
            if "@current_hostname" in line:
                self.logger.debug('Skipping: %s', line.rstrip())
                continue
            wr(line)
        self.logger.info('Processing fill_help_tables.sql')
        for line in (self.mysqld_pkgdir / 'fill_help_tables.sql').open():
            wr(line)


    def tail(self, pipe, prefix):
        '''
        Read lines from a pipe (such as process stdout/stderr) and print them with a prefix.
        '''
        def f():
            while True:
                line = pipe.readline()
                if not line:
                    break
                self.logger.debug(prefix + line.rstrip())
        t = threading.Thread(target=f)
        t.start()


    def terminate(self, p, name):
        '''
        Terminate process if it is still running.
        '''
        try:
            if p.poll() is None:
                self.logger.info('Terminating %s', name)
                p.terminate()
                rc = p.wait()
                self.logger.info('Process %s exited with return code %s', name, rc)
        except Exception as e:
            self.logger.error('Failed to terminate %s: %r', name, e)



if __name__ == '__main__':
    main()
