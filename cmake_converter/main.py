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

import argparse
import os

from cmake_converter.cmake import CMake
from cmake_converter.convertdata import ConvertData
from cmake_converter.message import send
from cmake_converter.vcxproj import Vcxproj


def main():
    """
    Main script : define arguments and send to ConvertData.

    """

    data = {
        'vcxproj': None,
        'cmake': None,
        'additional_code': None,
        'includes': None,
        'dependencies': None,
        'cmake_output': None,
        'data': None
    }

    usage = "cmake-converter -p <vcxproj>"
    # Init parser
    parser = argparse.ArgumentParser(
        usage=usage,
        description='Convert Visual Studio projects (.vcxproj) to CMakeLists.txt'
    )
    parser.add_argument('-p', '--project',
                        help='[required] valid vcxproj file. i.e.: ../../mylib.vcxproj',
                        dest='project'
                        )
    parser.add_argument('-o', '--output',
                        help='define output of CMakeLists.txt file',
                        dest='output'
                        )
    parser.add_argument('-a', '--additional',
                        help='import cmake code from file.cmake to your final CMakeLists.txt',
                        dest='additional'
                        )
    parser.add_argument('-D', '--dependencies',
                        help='replace dependencies found in .vcxproj, separated by colons. '
                             'i.e.: external/zlib/cmake/:../../external/g3log/cmake/',
                        dest='dependencies'
                        )
    parser.add_argument('-O', '--cmakeoutput',
                        help='define output of artefact produces by CMake.',
                        dest='cmakeoutput'
                        )
    parser.add_argument('-i', '--include',
                        help='add include directories in CMakeLists.txt. Default : False',
                        dest='include', action="store_true", default=False
                        )

    # Get args
    args = parser.parse_args()

    # If not project, display help
    if not args.project:
        parser.print_help()
        exit(0)

    # Vcxproj Path
    if args.project is not None:
        temp_path = os.path.splitext(args.project)
        if temp_path[1] == '.vcxproj':
            send('Project to convert = ' + args.project, '')
            project = Vcxproj()
            project.create_data(args.project)
            data['vcxproj'] = project.vcxproj
        else:
            send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
            exit(1)

    # CMakeLists.txt output
    if args.output is not None:
        cmakelists = CMake()
        if os.path.exists(args.output):
            cmakelists.create_cmake(args.output)
            data['cmake'] = cmakelists.cmake
        else:
            send(
                'This path does not exist. CMakeList.txt will be generated in current directory.',
                'error'
            )
            cmakelists.create_cmake()
        data['cmake'] = cmakelists.cmake
    else:
        cmakelists = CMake()
        cmakelists.create_cmake()
        data['cmake'] = cmakelists.cmake

    # CMake additional Code
    if args.additional is not None:
        data['additional_code'] = args.additional

    # If replace Dependencies
    if args.dependencies is not None:
        data['dependencies'] = args.dependencies.split(':')

    # Define Output of CMake artefact
    if args.cmakeoutput is not None:
        data['cmake_output'] = args.cmakeoutput

    # Add include directories found in vcxproj
    data['includes'] = args.include

    # Give data to ConvertData()
    all_data = ConvertData(data)
    all_data.create_data()


if __name__ == "__main__":
    main()
