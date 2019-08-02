# -*- coding:utf-8 -*-


"""
https://docs.python.org/3/library/unittest.html#assert-methods
"""


__author__ = "Andres FR"


# import sys
import unittest
# # mock sys.argv with "patch": https://stackoverflow.com/a/27765993
# from unittest.mock import patch
# import io_anim_mvnx
# from io_anim_mvnx.utils import ArgumentParserForBlender

from os.path import join, dirname
from io_anim_mvnx.utils import resolve_path
from io_anim_mvnx.mvnx import Mvnx


class MvnxTest(unittest.TestCase):
    """
    """
    DATAPATH = resolve_path("data")
    TEST_DATAPATH = join(dirname(__file__), "data")
    # APFB = ArgumentParserForBlender
    # NUMBERS = [str(i) for i in range(1, 20)]

    def test_mvnx_loads(self):
        """
        """
        MVNX_SCHEMA = join(self.DATAPATH, "mvnx_schema_mpiea.xsd")
        MVNX = join(self.TEST_DATAPATH, "test_mocap.mvnx")
        Mvnx(MVNX, MVNX_SCHEMA)
