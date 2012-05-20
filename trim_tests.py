# -*- coding: utf-8 -*-

from collections import deque
from cStringIO import StringIO
import unittest

import trim
from trim import Trim


class Mock (object):

    def __init__(self, operations):
        self._operations = deque(operations)

    def __str__(self):
        rem = ", ".join("%s(*%s, **%s)=%s" % op for op in self._operations)
        return "<%s remaining operations: %s>" % (self.__class__.__name__, rem)

    def everything_called(self):
        return len(self._operations) == 0

    def __getattr__(self, name):
        def f(*args, **kwargs):
            if not self._operations:
                raise Exception(
                    "called unexpected command %r %r %r" %
                    (name, args, kwargs))

            (expectedName, expectedArgs, expectedKwArgs, response) = \
                self._operations[0]

            expectedArgs = tuple(expectedArgs)

            assert (
                name == expectedName and
                args == expectedArgs and
                kwargs == expectedKwArgs
            ), (
                "Expected call %r %r %r, called %r %r %r" % (
                    expectedName, expectedArgs, expectedKwArgs,
                    name, args, kwargs)
            )

            self._operations.popleft()
            return response
        return f


class MockTests (unittest.TestCase):

    def test_works(self):
        m = Mock([
            ("someMethod", ("arg1", "arg2"), {}, "response"),
        ])
        self.assertEqual(m.someMethod("arg1", "arg2"), "response")
        self.assertTrue(m.everything_called())

    def tests_raises_exception(self):
        m = Mock([
            ("someMethod", ("arg1", "arg2"), {}, "response"),
        ])
        self.assertRaises(AssertionError, m.someOhterMethod)
        self.assertFalse(m.everything_called())


class TrimTests (unittest.TestCase):

    def test_trim_line(self):
        self.assertEqual(trim.trim_line(""), "")
        self.assertEqual(trim.trim_line(" "), "")
        self.assertEqual(trim.trim_line(" \n"), "\n")
        self.assertEqual(trim.trim_line(" \r\n"), "\r\n")
        self.assertEqual(trim.trim_line("a"), "a")
        self.assertEqual(trim.trim_line("a "), "a")
        self.assertEqual(trim.trim_line("a \n"), "a\n")
        self.assertEqual(trim.trim_line("a \r\n"), "a\r\n")
        self.assertEqual(trim.trim_line("abc abc"), "abc abc")
        self.assertEqual(trim.trim_line("abc abc "), "abc abc")
        self.assertEqual(trim.trim_line("abc abc \n"), "abc abc\n")
        self.assertEqual(trim.trim_line("abc abc \r\n"), "abc abc\r\n")

    def test_trim_file(self):
        fs = Mock([
            ("stat", ["."], {}, trim.StatResult(isDir=True)),
            ("listdir", ["."], {}, ["hello.txt"]),
            ("stat", ["./hello.txt"], {}, trim.StatResult(size=7, isFile=True)),
            ("get_contents", ["./hello.txt"], {}, "Hello \n"),
            #("write", ["./hello.txt~", "Hello \n"], {}, None),
            ("write", ["./hello.txt", "Hello\n"], {}, None),
        ])
        outputStream = StringIO()
        t = Trim(fs=fs, stdout=outputStream)
        t.process(".")
        output = outputStream.getvalue()
        self.assertTrue(fs.everything_called(), fs)
        self.assertEqual(output, "./hello.txt\n")

    def test_ignore_dotfiles(self):
        fs = Mock([
            ("stat", ["."], {}, trim.StatResult(isDir=True)),
            ("listdir", ["."], {}, [".hello.txt"]),
        ])
        outputStream = StringIO()
        t = Trim(fs=fs, stdout=outputStream)
        t.process(".")
        output = outputStream.getvalue()
        self.assertTrue(fs.everything_called())
        self.assertEqual(output, "")

    def test_ignore_known_binary_files(self):
        fs = Mock([
            ("stat", ["."], {}, trim.StatResult(isDir=True)),
            ("listdir", ["."], {}, ["image.png", "somescript.pyc"]),
        ])
        outputStream = StringIO()
        t = Trim(fs=fs, stdout=outputStream)
        t.process(".")
        output = outputStream.getvalue()
        self.assertTrue(fs.everything_called())
        self.assertEqual(output, "")

    def test_ignore_too_big_files(self):
        fs = Mock([
            ("stat", ["."], {}, trim.StatResult(isDir=True)),
            ("listdir", ["."], {}, ["somebigfile"]),
            ("stat", ["./somebigfile"], {}, trim.StatResult(size=1001001, isFile=True)),
        ])
        outputStream = StringIO()
        t = Trim(fs=fs, stdout=outputStream)
        t.process(".")
        output = outputStream.getvalue()
        self.assertTrue(fs.everything_called())
        self.assertEqual(output, "")

    def test_trim_file_dry_run(self):
        fs = Mock([
            ("stat", ["."], {}, trim.StatResult(isDir=True)),
            ("listdir", ["."], {}, ["hello.txt"]),
            ("stat", ["./hello.txt"], {}, trim.StatResult(size=7, isFile=True)),
            ("get_contents", ["./hello.txt"], {}, "Hello \n"),
        ])
        outputStream = StringIO()
        t = Trim(fs=fs, stdout=outputStream, dryRun=True)
        t.process(".")
        output = outputStream.getvalue()
        self.assertTrue(fs.everything_called(), fs)
        self.assertEqual(output, "./hello.txt\n")



if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))


