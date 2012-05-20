#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Instant Apache.
"""

import optparse
import os
import subprocess
import threading
from os.path import abspath, isdir, isfile, join as path_join


possibleApachePaths = [
    "/opt/local/apache2/bin/httpd",
]


def find_apache_executable():
    for path in possibleApachePaths:
        if not isfile(path):
            continue
        return path
    return None


class InstantApacheError (Exception):
    pass


class ReadThread (object):

    def __init__(self, f, name):
        self.f = f
        self.name = name
        self.thread = None

    def start(self):
        assert self.thread is None
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        return self

    def _run(self):
        while True:
            line = self.f.readline()
            if line == "":
                print "%s EOF" % self.name
                break
            print "%s: %s" % (self.name, line.rstrip())


class TailThread (object):

    def __init__(self, path, name):
        self.path = path
        self.name = name
        self.tailProcess = None
        self.readThread = None

    def start(self):
        self.tailProcess = subprocess.Popen(["gtail", "-n", "0", "-s", "0.1", "-f", self.path], stdout=subprocess.PIPE)
        self.readThread = ReadThread(self.tailProcess.stdout, self.name)
        self.readThread.start()
        return self


class InstantApache (object):

    def __init__(self, port=4000, apacheExecutable=None, documentRoot=None):
        self.port = port
        self.apacheProcess = None
        if apacheExecutable:
            self.apacheExecutable = apacheExecutable
        else:
            self.apacheExecutable = find_apache_executable()

        if documentRoot:
            self.documentRoot = documentRoot
        else:
            self.documentRoot = abspath(".")

        self.envDir = abspath("instant-apache-env")
        if not isdir(self.envDir):
            os.mkdir(self.envDir)
        self.configFilePath = path_join(self.envDir, "apache.conf")
        self.errorLogPath = path_join(self.envDir, "error.log")
        self.pidFilePath = path_join(self.envDir, "httpd.pid")

        self.tailThreads = list()


    def start(self):
        self.generate_configuration()

        if not self.apacheExecutable:
            raise InstantApacheError("Apache executable path not set")
        args = [self.apacheExecutable, "-f", self.configFilePath, "-D", "FOREGROUND"]
        self.apacheProcess = subprocess.Popen(
            args,
            stdin=open("/dev/null"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True)

        assert not self.tailThreads
        self.tailThreads.append(ReadThread(self.apacheProcess.stdout, "apache stdout").start())
        self.tailThreads.append(ReadThread(self.apacheProcess.stderr, "apache stderr").start())
        self.tailThreads.append(TailThread(self.errorLogPath, "apache error log").start())

    def stop(self):
        pass

    def generate_configuration(self):
        with open(self.configFilePath, "w") as f:
            f.write("# This is configration file for Apache process "
                    "spawned by instant_apache utility.\n")
            f.write("Listen 127.0.0.1:%d\n" % self.port)
            f.write('ServerRoot "%s"\n' % self.envDir)
            f.write('PidFile "%s"\n' % self.pidFilePath)
            f.write('ErrorLog "%s"\n' % self.errorLogPath)
            f.write("LogLevel info\n")
            f.write('DocumentRoot "%s"\n' % self.documentRoot)
            f.write('LoadModule authz_host_module /opt/local/apache2/modules/mod_authz_host.so\n')
            f.write('LoadModule dir_module /opt/local/apache2/modules/mod_dir.so\n')
            f.write('LoadModule mime_magic_module /opt/local/apache2/modules/mod_mime_magic.so\n')
            f.write('LoadModule mime_module /opt/local/apache2/modules/mod_mime.so\n')
            f.write('LoadModule rewrite_module /opt/local/apache2/modules/mod_rewrite.so\n')
            f.write('LoadModule php5_module /opt/local/apache2/modules/libphp5.so\n')
            f.write('<IfModule mod_php5.c>\n')
            f.write('    AddType  application/x-httpd-php         .php\n')
            f.write('    AddType  application/x-httpd-php-source  .phps\n')
            f.write('</IfModule>\n')
            f.write('<Directory />\n')
            f.write('    Options FollowSymLinks\n')
            f.write('    AllowOverride None\n')
            f.write('    Order deny,allow\n')
            f.write('    Deny from all\n')
            f.write('</Directory>\n')
            f.write('<Directory "%s">\n' % self.documentRoot)
            f.write('    Options Indexes FollowSymLinks\n')
            f.write('    AllowOverride all\n')
            f.write('    Order allow,deny\n')
            f.write('    Allow from all\n')
            f.write('</Directory>\n')
            f.write('<IfModule dir_module>\n')
            f.write('    DirectoryIndex index.html index.php\n')
            f.write('</IfModule>\n')
            f.write('<IfModule mime_module>\n')
            f.write('    TypesConfig /opt/local/apache2/conf/mime.types\n')
            f.write('</IfModule>\n')



def main():
    op = optparse.OptionParser()
    op.add_option("--document-root", dest="documentRoot", default=".")
    (options, args) = op.parse_args()

    ia = InstantApache(
        documentRoot=abspath(options.documentRoot))
    ia.start()
    try:
        ia.apacheProcess.wait()
    except Exception, e:
        print e





if __name__ == "__main__":
    main()

