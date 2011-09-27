# -*- coding: utf-8 -*-

import unittest
from cStringIO import StringIO

import svnlog


class SvnLogTests (unittest.TestCase):


    def test_revision_is_correctly_parsed_from_svn_log_header_line(self):
        self.assertEqual(svnlog.parse_revision_from_header("r13 | author ..."), 13)


    def test_svn_log_output_is_correctly_parsed(self):
        svnLogOutput = StringIO(
            "------------------------------------------------------------------------\n"
            "r2 | messa | 2011-09-21 20:05:38 +0200 (Wed, 21 Sep 2011) | 1 line\n"
            "\n"
            "second commit\n"
            "------------------------------------------------------------------------\n"
            "r1 | messa | 2011-09-21 20:00:20 +0200 (Wed, 21 Sep 2011) | 1 line\n"
            "\n"
            "first commit\n"
            "------------------------------------------------------------------------\n"
        )
        data = list(svnlog.parse_svn_log_output(svnLogOutput))
        self.assertEqual(data, [
            (2, "r2 | messa | 2011-09-21 20:05:38 +0200 (Wed, 21 Sep 2011) | 1 line\n", "second commit\n"),
            (1, "r1 | messa | 2011-09-21 20:00:20 +0200 (Wed, 21 Sep 2011) | 1 line\n", "first commit\n")
        ])


    def test_main_works_as_expected(self):

        class FakeProcess (object):
            """
            Imitates subprocess.Popen objects.
            """

            def __init__(self, stdout):
                self.stdout = StringIO(stdout)

            def wait(self):
                return 0

        class Commands (object):

            def run_svn_log(self):
                return FakeProcess(stdout=(
                    "------------------------------------------------------------------------\n"
                    "r2 | messa | 2011-09-21 20:05:38 +0200 (Wed, 21 Sep 2011) | 1 line\n"
                    "\n"
                    "second commit\n"
                    "------------------------------------------------------------------------\n"
                    "r1 | messa | 2011-09-21 20:00:20 +0200 (Wed, 21 Sep 2011) | 1 line\n"
                    "\n"
                    "first commit\n"
                    "------------------------------------------------------------------------\n"
                ))

            def run_svn_diff(self, revision):
                if revision == 1:
                    return FakeProcess(stdout=(
                        "Index: somefile.txt\n"
                        "===================================================================\n"
                        "--- somefile.txt        (revision 0)\n"
                        "+++ somefile.txt        (revision 1)\n"
                        "@@ -0,0 +1 @@\n"
                        "+Hello, World!\n"))
                elif revision == 2:
                    return FakeProcess(stdout=(
                        "Index: somefile.txt\n"
                        "===================================================================\n"
                        "--- somefile.txt        (revision 1)\n"
                        "+++ somefile.txt        (revision 2)\n"
                        "@@ -1 +1 @@\n"
                        "-Hello, World!\n"
                        "+Lorem ipsum.\n"))
                else:
                    raise Exception("Unknown revision")

            def run_colordiff(self, stdin):
                raise OSError(2, "x")


        outputStream = StringIO()

        svnlog.main(out=outputStream, commands=Commands())

        output = outputStream.getvalue()

        desiredOutput = (
            "//////////////////////////////////////////////////////////////////////////////\n"
            "//////////////////////////////////////////////////////////////////////////////\n"
            "r2 | messa | 2011-09-21 20:05:38 +0200 (Wed, 21 Sep 2011) | 1 line\n"
            "\n"
            "second commit\n"
            "\n"
            "Index: somefile.txt\n"
            "===================================================================\n"
            "--- somefile.txt        (revision 1)\n"
            "+++ somefile.txt        (revision 2)\n"
            "@@ -1 +1 @@\n"
            "-Hello, World!\n"
            "+Lorem ipsum.\n"
            "//////////////////////////////////////////////////////////////////////////////\n"
            "//////////////////////////////////////////////////////////////////////////////\n"
            "r1 | messa | 2011-09-21 20:00:20 +0200 (Wed, 21 Sep 2011) | 1 line\n"
            "\n"
            "first commit\n"
            "\n"
            "Index: somefile.txt\n"
            "===================================================================\n"
            "--- somefile.txt        (revision 0)\n"
            "+++ somefile.txt        (revision 1)\n"
            "@@ -0,0 +1 @@\n"
            "+Hello, World!\n")

        self.assertEqual(output, desiredOutput)


    def test_main_prints_out_correct_error_message_when_not_in_svn_repository(self):

        class FakeProcess (object):
            """
            Imitates subprocess.Popen objects.
            """

            def __init__(self, stdout, stderr="", retcode=0):
                self.stdout = StringIO(stdout)
                self.stderr = StringIO(stderr)
                self.retcode = retcode

            def wait(self):
                return self.retcode

        class Commands (object):

            def run_svn_log(self):
                return FakeProcess(stdout="", stderr="svn: '.' is not a working copy\n", retcode=1)

        outputStream = StringIO()
        errorOutputStream = StringIO()
        self.assertRaises(SystemExit, svnlog.main, out=outputStream, err=errorOutputStream, commands=Commands())
        output = outputStream.getvalue()
        errorOutput = errorOutputStream.getvalue()
        self.assertEqual(errorOutput, "svn: '.' is not a working copy\n")
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))



