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
    Main
    ====
     Manage script arguments and launch
"""

import argparse
import re
import os

from cmake_converter.data_converter import DataConverter


def convert_project(data, vcxproj, cmake_dest_dir, references=False):
    """
    Convert a ``vcxproj`` to a ``CMakeLists.txt``

    :param data: input data of user
    :type data: dict
    :param vcxproj: input vcxproj
    :type vcxproj: str
    :param references: input vcxproj
    :param cmake_dest_dir: destinaton folder of CMakeLists.txt
    :type cmake_dest_dir: str
    """

    # Give data to DataConverter()
    data_converter = DataConverter(data)
    data_converter.init_files(vcxproj, cmake_dest_dir)
    data_converter.create_data(references)

    # Close CMake file
    data_converter.close_cmake_file()

    # If the current VS Project had references, create the corresponding CMakeLists
    if data_converter.referenced_projs:
        for proj in data_converter.referenced_projs:
            convert_project(data, proj['vcxproj'], proj['cmake'], references=True)


def main():  # pragma: no cover
    """
    Define arguments and send to DataConverter()

    """

    data = {
        'vcxproj': None,
        'cmake': None,
        'additional_code': None,
        'includes': None,
        'dependencies': None,
        'cmake_output': None,
        'data': None,
        'std': None,
    }

    usage = "cmake-converter -p <vcxproj> [-c | -a | -D | -O | -i | -std]"
    # Init parser
    parser = argparse.ArgumentParser(
        usage=usage,
        description='Convert Visual Studio projects (.vcxproj) to CMakeLists.txt'
    )
    parser.add_argument(
        '-s', '--solution',
        help='valid solution file. i.e.: ../../my.sln',
        dest='solution'
    )
    parser.add_argument(
        '-p', '--project',
        help='[required] valid vcxproj file. i.e.: ../../mylib.vcxproj',
        dest='project'
    )
    parser.add_argument(
        '-c', '--cmake',
        help='define output of CMakeLists.txt file',
        dest='cmake'
    )
    parser.add_argument(
        '-a', '--additional',
        help='import cmake code from file.cmake to your final CMakeLists.txt',
        dest='additional'
    )
    parser.add_argument(
        '-D', '--dependencies',
        help='replace dependencies found in .vcxproj, separated by colons. '
             'i.e.: external/zlib/cmake/:../../external/g3log/cmake/',
        dest='dependencies'
    )
    parser.add_argument(
        '-O', '--cmakeoutput',
        help='define output of artefact produces by CMake.',
        dest='cmakeoutput'
    )
    parser.add_argument(
        '-i', '--include',
        help='add include directories in CMakeLists.txt. Default : False',
        dest='include', action="store_true", default=False
    )
    parser.add_argument(
        '-std', '--std',
        help='choose your C++ std version. Default : c++11',
        dest='std'
    )

    # Get args
    args = parser.parse_args()

    # Prepare data
    if not args.project and not args.solution:
        parser.print_help()
        exit(0)

    data['additional_code'] = args.additional
    if args.dependencies:
        data['dependencies'] = args.dependencies.split(':')
    data['cmake_output'] = args.cmakeoutput
    data['includes'] = args.include

    if args.std:
        data['std'] = args.std

    if not args.solution:
        cmake_lists_path = os.path.dirname(args.project)
        if args.cmake:
            cmake_lists_path = args.cmake
        convert_project(data, args.project, cmake_lists_path)
    else:
        sln = open(args.solution)
        slnpath = os.path.dirname(args.solution)
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
