#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017:
#   Matthieu Estrada, ttamalfor@gmail.com
#
# This file is part of (CMakeConverter).
#
# (CMakeConverter) is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# (CMakeConverter) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with (CMakeConverter).  If not, see <http://www.gnu.org/licenses/>.

"""
CMake-Converter command line interface::

    Usage:
        cmake-converter [-h]
        cmake-converter [-V]
        cmake-converter (-s solution | -p project) [-i]
                        [-c cmake]
                        [-D dependency:dependency:...]
                        [-O cmakeoutput]
                        [-a codefile]
                        [-I cmakefile]
                        [-S std]

    Options:
        -h, --help                  Show this help message and exit
        -V, --version               Show application version
        -s, --solution=solution     Path to a MSVC solution (.sln) (BETA)
        -p, --project=project       Path to a MSVC project (.vcxproj)
        -c, --cmake=cmake           Specify output of generated CMakeLists.txt
        -D, --dependencies=dep      Replace dependencies found in ".vcxproj" file, separated by
                                    colons
        -O, --cmakeoutput=output    Define output of artefact produces by CMake.
        -i, --include               Add include directories in CMakeLists.txt. [default: False]
        -a, --additional=file       Import cmake code from any file to generated CMakeLists.txt.
        -I, --includecmake=file     Add Include directive for given file in CMakeLists.txt.
        -S, --std=std               Choose your C++ std version. [default: c++11]


    Use cases:
        Display help message:
            cmake-converter (-h | --help)
        Display current version:
            cmake-converter (-V | --version)
        Convert an MSVC project and defines output of artefacts:
            cmake-converter -p ../msvc/foo/foo.vcxproj -c ../cmake/foo -O ../build/compiler
        Convert an MSVC project and add ".cmake" file:
            cmake-converter -p ../msvc/foo/foo.vcxproj -I ../cmake/foo/file.cmake
        Convert an MSVC project with specific STD version:
            cmake-converter -p ../msvc/foo/foo.vcxproj -c ../cmake/foo -S c++17

    Hint and tips:
        The solution conversion is still in BETA and may therefore have some problems !

        It is important to check that the generated CMake files are working properly before using
        them in production.

        CMake Converter only manage Debug and Release build types. You can provide the build type
        by add "-DCMAKE_BUILD_TYPE=<BUILD_TYPE>" to cmake command.

        CMake-Converter will try to respect as much as possible the data of your MSVC project.
        However, it is necessary to pay attention to the relative paths of the files.

        If your project is in the following path: "../msvc/foo", your CMakeLists file should have
        the same tree level. The same is to be done for the files to include !
"""

import re
import os

from docopt import docopt, DocoptExit

from cmake_converter import __version__
from cmake_converter.utils import message
from cmake_converter.data_converter import DataConverter


def convert_project(data, vcxproj, cmake_lists):
    """
    Convert a ``vcxproj`` to a ``CMakeLists.txt``

    :param data: input data of user
    :type data: dict
    :param vcxproj: input vcxproj
    :type vcxproj: str
    :param cmake_lists: destinaton folder of CMakeLists.txt
    :type cmake_lists: str
    """

    # Give data to DataConverter()
    data_converter = DataConverter(data)
    data_converter.init_files(vcxproj, cmake_lists)
    data_converter.create_data()

    # Close CMake file
    data_converter.close_cmake_file()


def main():  # pragma: no cover
    """
    Define arguments and send to DataConverter()

    """

    # Get command line parameters
    args = None
    try:
        args = docopt(__doc__, version=__version__)
    except DocoptExit as exp:
        message("Command line parsing error:\n%s." % exp, 'error')
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Exiting with error code: 64")
        exit(64)

    # Check input file
    if not args['--project'] and not args['--solution']:
        message('You must specify a project or solution !', 'warn')
        print(__doc__)
        exit(2)

    # Prepare data
    data = {}
    for key in args:
        data[key.replace('--', '')] = args[key]

    # Convert
    if not data['solution']:
        if data['cmake']:
            cmake_lists_path = data['cmake']
        else:
            cmake_lists_path = os.path.dirname(data['project'])
        convert_project(data, data['project'], cmake_lists_path)
    else:
        sln = open(data['solution'])
        slnpath = os.path.dirname(data['solution'])
        p = re.compile(r', "(.*\.vcxproj)"')
        projects = p.findall(sln.read())
        sln.close()
        for project in projects:
            project = '/'.join(project.split('\\'))
            project_abs = os.path.join(slnpath, project)
            convert_project(data, project_abs, os.path.dirname(project_abs))
            print('\n')


if __name__ == "__main__":  # pragma: no cover
    main()
