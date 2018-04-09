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
from cmake_converter.data_files import get_cmake_lists


def convert_project(converter_args, vcxproj_path, cmake_lists_destination_path):
    """
    Convert a ``vcxproj`` to a ``CMakeLists.txt``

    :param converter_args: input data of user
    :type converter_args: dict
    :param vcxproj_path: input vcxproj
    :type vcxproj_path: str
    :param cmake_lists_destination_path: Destination folder of CMakeLists.txt
    :type cmake_lists_destination_path: str
    """

    # Give data to DataConverter()
    data_converter = DataConverter(converter_args)
    data_converter.init_files(vcxproj_path, cmake_lists_destination_path)
    data_converter.create_data()

    # Close CMake file
    data_converter.close_cmake_file()


def main():  # pragma: no cover
    """
    Define arguments and send to DataConverter()

    """

    converter_args = {
        'vcxproj': None,
        'cmake': None,
        'additional_code': None,
        'includes': None,
        'dependencies': None,
        'cmake_output': None,
        'data': None,
        'std': None,
        'is_converting_solution': False,
        'configuration_types': set(),
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

    # Prepare converter_args
    if not args.project and not args.solution:
        parser.print_help()
        exit(0)

    converter_args['additional_code'] = args.additional
    if args.dependencies:
        converter_args['dependencies'] = args.dependencies.split(':')
    converter_args['cmake_output'] = args.cmakeoutput
    converter_args['includes'] = args.include

    if args.std:
        converter_args['std'] = args.std

    if not args.solution:
        cmake_lists_path = os.path.dirname(args.project)
        if args.cmake:
            cmake_lists_path = args.cmake
        convert_project(converter_args, args.project, cmake_lists_path)
    else:
        converter_args['is_converting_solution'] = True
        sln = open(args.solution)
        solution_path = os.path.dirname(args.solution)
        p = re.compile(r', "(.*\.vcxproj)"')
        projects = p.findall(sln.read())
        sln.close()

        sln_cmake = get_cmake_lists(solution_path)
        DataConverter.add_cmake_version_required(sln_cmake)
        sln_cmake.write('project({0})\n\n'. format(os.path.splitext(os.path.basename(args.solution))[0]))
        subdirectories = []
        for project in projects:
            project = '/'.join(project.split('\\'))
            project_abs = os.path.join(solution_path, project)
            subdirectory = os.path.dirname(project_abs)
            convert_project(converter_args, project_abs, subdirectory)
            cmake_dir = os.path.dirname(converter_args['cmake'].name)
            subdirectories.append(os.path.relpath(cmake_dir, solution_path))
            print('\n')
        # TODO: try to write configuration types for each project locally due possible difference.
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Global configuration types\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('set(CMAKE_CONFIGURATION_TYPES\n')
        configuration_types_list = list(converter_args['configuration_types'])
        configuration_types_list.sort(key=str.lower)
        for configuration_type in configuration_types_list:
            sln_cmake.write('    \"{0}\"\n'.format(configuration_type))
        sln_cmake.write('    CACHE TYPE INTERNAL FORCE\n)\n\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Global compiler options\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('if(MSVC)\n')
        sln_cmake.write('  # remove default flags provided with CMake for MSVC\n')
        sln_cmake.write('  set(CMAKE_CXX_FLAGS "")\n')
        sln_cmake.write('  set(CMAKE_CXX_FLAGS_RELEASE "")\n')
        sln_cmake.write('  set(CMAKE_CXX_FLAGS_DEBUG "")\n')
        sln_cmake.write('endif()\n\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Global linker options\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('if(MSVC)\n')
        sln_cmake.write('  # remove default flags provided with CMake for MSVC\n')
        sln_cmake.write('  set(CMAKE_EXE_LINKER_FLAGS "")\n')
        sln_cmake.write('  set(CMAKE_MODULE_LINKER_FLAGS "")\n')
        sln_cmake.write('  set(CMAKE_SHARED_LINKER_FLAGS "")\n')
        sln_cmake.write('  set(CMAKE_STATIC_LINKER_FLAGS "")\n')
        sln_cmake.write('endif()\n\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Additional Global Settings(add specific info there)\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('include(CMake/GlobalSettingsInclude.cmake)\n\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Sub-projects\n')
        sln_cmake.write('################################################################################\n')
        subdirectories.sort(key=str.lower)
        for subdirectory in subdirectories:
            sln_cmake.write('add_subdirectory({0})\n'.format(subdirectory.replace('\\', '/')))
        sln_cmake.write('\n')
        sln_cmake.close()


if __name__ == "__main__":  # pragma: no cover
    main()
