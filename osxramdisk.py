#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-

import optparse
import re
import subprocess
import sys

assert hasattr(subprocess, "check_output"), "Are you using Python 2.7+?"


def parse_size(s):
    """
    Velikost zadanou v jakýchkoliv obvyklých jednotkách vrací v bajtech.
    """
    assert isinstance(s, basestring)
    m = re.match(r'^([0-9]+) *([^0-9]*)$', s)
    if not m:
        raise Exception("Failed to parse size %r" % s)
    n = int(m.group(1))
    unit = m.group(2)
    if not unit:
        return n
    if unit.lower() in ("k", "kb"):
        return n * 2**10
    if unit.lower() in ("m", "mb"):
        return n * 2**20
    if unit.lower() in ("g", "gb"):
        return n * 2**30
    raise Exception("Unknown unit %s" % unit)


assert parse_size("1k") == 2**10
assert parse_size("1K") == 2**10
assert parse_size("1kB") == 2**10
assert parse_size("1KB") == 2**10
assert parse_size("1m") == 2**20
assert parse_size("1M") == 2**20
assert parse_size("1MB") == 2**20
assert parse_size("1g") == 2**30
assert parse_size("1G") == 2**30
assert parse_size("1GB") == 2**30


def main():
    if sys.platform != "darwin":
        print "Warning: this script is designed for darwin (Mac OS X); your " \
            "platform is %s" % sys.platform
    
    op = optparse.OptionParser()
    op.add_option("--mountpoint", default="/Volumes/ramdisk")
    op.add_option("--size", default="200M")
    (options, args) = op.parse_args()

    size = parse_size(options.size)
    if already_mounted(options.mountpoint):
        raise Exception("Some filesystem is already mounted at %s" % options.mountpoint)
    device_name = create_ramdisk_device(size)
    create_filesystem(device_name)
    mount(device_name, options.mountpoint)
    print "Done."
    print ""
    print "If you want to use the ramdisk as TMPDIR, run these commands:"
    print ""
    print "TMPDIR=%s; export TMPDIR" % options.mountpoint
    tmpdir = os.getenv("TMPDIR")
    if tmpdir:
        print ""
        print "(Current TMPDIR is %s)" % tmpdir


def already_mounted(mountpoint):
    output = subprocess.check_output(["mount"])
    for n, line in enumerate(output.splitlines()):
        m = re.match(r"^(.*) on (/.*) (\(.*\))$", line)
        if not m:
            raise Exception(
                "Failed to parse line %d of output of the command mount: %s" %
                (n, line))
        location = m.group(2)
        if location == mountpoint:
            return True
    return False


def create_ramdisk_device(size):
    assert isinstance(size, int)
    print "Creating ramdisk device with size %.2f MB" % (size / 2.**20)
    sectors = size / 512
    output = subprocess.check_output(
        ["hdiutil", "attach", "-nomount", "ram://%d" % sectors])
    if not re.match(r"^/dev/disk[0-9]+$", output.strip()):
        raise Exception("Invalid hdiutil output: %r", output)
    print "Created device %s" % output
    return output


def create_filesystem(device_name):
    print "Checking whether %s contains no data" % device_name
    with open(device_name, "r") as f:
        block = f.read(4096)
        assert block == "\0" * len(block)
    print "Creating HFS filesystem on %s" % device_name
    subprocess.check_output(["newfs_hfs", device_name])


def mount(device_name, mountpoint):
    print "Mounting %s on %s" % (device_name, mountpoint)
    subprocess.check_output(
        ["mount", "-o", "noatime", "-t", "hfs", device_name, mountpoint])


if __name__ == "__main__":
    try:
        main()
    except Exception, e:
        print >>sys.stderr, "Error: %s" % e
        exit(1)

