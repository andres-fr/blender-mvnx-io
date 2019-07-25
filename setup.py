# -*- coding:utf-8 -*-


"""
Build script for the package. It has to be in the repository root directory.
Make sure that the config entries are correct!
"""

import setuptools


def setup():
    """
    The proper setup function, adapted from the tutorial in
    https://packaging.python.org/tutorials/packaging-projects/
    """
    with open("README.md", "r") as f:
        long_description = f.read()
    #
    setuptools.setup(
        name="io_anim_mvnx",
        version="0.1.0",
        author="Andres FR",
        author_email="andres-fr@users.noreply.github.com",
        description="Blender add-on for I/O of MVNX MoCap data",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/andres-fr/blender-mvnx-io",
        packages=setuptools.find_packages(exclude=["*utest"]),
        include_package_data=True,
        classifiers=[
            # comprehensive list: https://pypi.org/classifiers/
            "Programming Language :: Python :: 3 :: Only",
            # "Programming Language :: Python",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            # "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent"
        ],
    )


if __name__ == "__main__":
    setup()
