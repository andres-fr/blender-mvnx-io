# -*- coding:utf-8 -*-


"""
This module contains a simple test that always passes.
It can be useful to make sure that the testing facilities
are working.
"""


__author__ = "Andres FR"


import unittest


class Tautology(unittest.TestCase):
    """
    Contains a simple test that always passes
    """

    def test_tautology(self):
        """
        A  simple test that always passes
        """
        self.assertTrue(True)
