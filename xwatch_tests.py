# -*- coding: utf-8 -*-

import unittest
from cStringIO import StringIO

import xwatch


class XWatchTests (unittest.TestCase):

    def test_works_as_expected(self):
        outputStream = StringIO()

        class TestTerminal (object):
            def get_height(self):
                return 5
            def gray(self):
                outputStream.write("[GRAY]")
            def reset_colors(self):
                outputStream.write("[RESET_COLORS]")

        class TestStopwatch (object):
            def __init__(self):
                self.started = False
            def start(self):
                self.started = True
            def stop(self):
                assert self.started
                self.started = False
            @property
            def duration(self):
                return 0.08

        def testGetTime():
            return "10:11:12"

        xw = xwatch.XWatch(
            terminal=TestTerminal(), stopwatch=TestStopwatch(),
            getTime=testGetTime, stdout=outputStream)
        xw.command = "echo hello"

        xw.run_one()
        output = outputStream.getvalue()

        desiredOutput = (
            "\n"
            "\n"
            "hello\n"
            "[GRAY]echo hello  10:11:12  0.080 s[RESET_COLORS]\n"
        )

        self.assertEqual(output, desiredOutput)


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))

