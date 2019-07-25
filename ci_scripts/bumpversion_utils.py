# -*- coding:utf-8 -*-


"""
This module provides functionality to retrieve the information in the
bumpversion config file the same way as bumpversion does.
"""


__author__ = "Andres FR"


import argparse
#
from configparser import ConfigParser
from packaging import version


def get_bumpversion(bumpversion_filepath, as_tuple=False):
    """
    Given the path to the .bumpversion.cfg file, this function
    returns its current_version field, either as string (default)
    or as tuple.
    """
    parser = ConfigParser("")
    # don't transform keys to lowercase (which would be the default)
    parser.optionxform = lambda option: option
    # parser.add_section('bumpversion')
    with open(bumpversion_filepath, 'rt', encoding='utf-8') as f:
        parser.read_file(f)
        v = version.parse(parser["bumpversion"]["current_version"])
        return v.release if as_tuple else v.public


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--as_tuple",
                        action="store_true",
                        help="Retrieve version as tuple, otherwise as string.")
    parser.add_argument("-f", "--bumpversion_config_file",
                        type=str, required=True,
                        help="Filepath to the .bumpversion.cfg to examine.")
    args = parser.parse_args()
    #
    FILEPATH = args.bumpversion_config_file
    AS_TUPLE = args.as_tuple
    v = get_bumpversion(FILEPATH, AS_TUPLE)
    print("version:", v)
