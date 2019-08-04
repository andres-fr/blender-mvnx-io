# -*- coding:utf-8 -*-


"""
https://docs.python.org/3/library/unittest.html#assert-methods
"""


__author__ = "Andres FR"


import sys
import unittest
# mock sys.argv with "patch": https://stackoverflow.com/a/27765993
from unittest.mock import patch
from io_anim_mvnx.utils import ArgumentParserForBlender


class ArgparserTest(unittest.TestCase):
    """
    Mock the sys.argv and test the ArgumentParserForBlender.
    """
    APFB = ArgumentParserForBlender
    NUMBERS = [str(i) for i in range(1, 20)]

    def test_no_doubledash(self):
        """
        """
        testargv = self.NUMBERS
        # outside "with", sys.argv is still the complete CLI call
        with patch.object(sys, 'argv', testargv):
            # in this context sys.argv is testargv
            apfb = self.APFB()
            argv_after = apfb.get_argv_after_doubledash(sys.argv)
            self.assertEqual(argv_after, [])

    def test_one_doubledash(self):
        """
        """
        testargv = self.NUMBERS
        p = 5  # position of the double-dash
        testargv.insert(p, "--")
        # outside "with", sys.argv is still the complete CLI call
        with patch.object(sys, 'argv', testargv):
            # in this context sys.argv is testargv
            apfb = self.APFB()
            argv_after = apfb.get_argv_after_doubledash(sys.argv)
            self.assertEqual(argv_after, self.NUMBERS[p+1:])

    def test_two_doubledashes(self):
        """
        As expected, cuts after the first match.
        """
        testargv = self.NUMBERS
        p1, p2 = 2, 6
        testargv.insert(p1, "--")
        testargv.insert(p2, "--")
        # outside "with", sys.argv is still the complete CLI call
        with patch.object(sys, 'argv', testargv):
            # in this context sys.argv is testargv
            apfb = self.APFB()
            argv_after = apfb.get_argv_after_doubledash(sys.argv)
            self.assertEqual(argv_after, self.NUMBERS[p1+1:])

    def test_undefined_call(self):
        """
        The arguments are passed properly, but the arg parser raises
        an exception since they aren't defined:
        """
        testargv = ["blender", "-b", "somefile.blend", "--quack", "3",
                    "--python", "script.py", "--", "-a", "1", "-b", "2"]
        with patch.object(sys, 'argv', testargv):
            # in this context sys.argv is testargv
            apfb = self.APFB()
            self.assertRaises(SystemExit, apfb.parse_args)

    def test_defined_call(self):
        """
        The arguments are passed and defined properly, all works
        """
        testargv = ["blender", "-b", "somefile.blend", "--quack", "3",
                    "--python", "script.py", "--", "-a", "1", "-b", "2"]
        python_args = {"a": 1, "b": 2}
        with patch.object(sys, 'argv', testargv):
            # in this context sys.argv is testargv
            apfb = self.APFB()
            apfb.add_argument("-a", type=int)
            apfb.add_argument("-b", type=int)
            arg_dict = vars(apfb.parse_args())
            self.assertEqual(arg_dict, python_args)
