# -*- coding:utf-8 -*-


"""
Since this directory is 'unrelated' to the package to be imported, we have
to tell Python where to find it. Import this file in every utest before
importing the package. Do this to bypass the flake8 'F401' error:

import environment  # noqa: F401
"""


__author__ = "Andres FR"


import sys
from os.path import abspath, dirname


MODULE_ROOT_DIR = dirname(dirname(abspath(__file__)))
# append module root directory to sys.path
if MODULE_ROOT_DIR not in sys.path:
    sys.path.append(MODULE_ROOT_DIR)
