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

from cmake_converter.data_converter import DataConverter, CPPConverter, FortranProjectConverter
from cmake_converter.data_files import get_cmake_lists
from cmake_converter.utils import set_unix_slash


def convert_project(context, xml_project_path, cmake_lists_destination_path):
    """
    Convert a ``vcxproj`` to a ``CMakeLists.txt``

    :param context: input data of user
    :type context: dict
    :param xml_project_path: input xml_proj
    :type xml_project_path: str
    :param cmake_lists_destination_path: Destination folder of CMakeLists.txt
    :type cmake_lists_destination_path: str
    """

    # Give data to DataConverter()
    data_converter = None
    if 'vcxproj' in xml_project_path:
        data_converter = CPPConverter(context)
    if 'vfproj' in xml_project_path:
        data_converter = FortranProjectConverter(context)
    if data_converter is None:
        return  # unknown project type
    data_converter.init_files(xml_project_path, cmake_lists_destination_path)
    data_converter.create_data()

    # Close CMake file
    data_converter.close_cmake_file()


def parse_solution(sln_text):
    """
    :param sln_text:
    :return: data from solution
    """
    projects_data = {}
    p = re.compile(r'(Project.*\s=\s\"(.*)\",\s\"(.*\.(.*proj))\",.*(\{.*\})(?:.|\n)*?EndProject(?!Section))')
    parsed_data = p.findall(sln_text)
    for project_data_match in parsed_data:
        project = dict()
        project['name'] = project_data_match[1]
        project['path'] = project_data_match[2]
        project['type'] = project_data_match[3]
        guid = project_data_match[4]
        if 'ProjectDependencies' in project_data_match[0]:
            project['sln_deps'] = []
            dependencies_section = re.compile(r'ProjectSection\(ProjectDependencies\) '
                                              r'= postProject(?:.|\n)*?EndProjectSection')
            dep_data = dependencies_section.findall(project_data_match[0])
            dependencies_guids = re.compile(r'((\{.*\}) = (\{.*\}))')
            guids_deps_matches = dependencies_guids.findall(dep_data[0])
            for guids_deps_match in guids_deps_matches:
                project['sln_deps'].append(guids_deps_match[2])
        projects_data[guid] = project

    # replace GUIDs with Project names in dependencies
    for project_guid in projects_data:
        project_data = projects_data[project_guid]
        if 'sln_deps' in project_data:
            target_deps = []
            dependencies_list = project_data['sln_deps']
            for dep_guid in dependencies_list:
                dep = projects_data[dep_guid]
                target_deps.append(dep['name'])
            project_data['sln_deps'] = target_deps
    return projects_data


def set_dependencies_for_project(context, project_data):
    context['sln_deps'] = []
    if 'sln_deps' not in project_data:
        return

    context['sln_deps'] = project_data['sln_deps']


def main():  # pragma: no cover
    """
    Define arguments and send to DataConverter()

    """

    context = {
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

    # Prepare context
    if not args.project and not args.solution:
        parser.print_help()
        exit(0)

    context['additional_code'] = args.additional
    if args.dependencies:
        context['dependencies'] = args.dependencies.split(':')
    context['cmake_output'] = args.cmakeoutput
    context['includes'] = args.include

    if args.std:
        context['std'] = args.std

    if not args.solution:
        cmake_lists_path = os.path.dirname(args.project)
        if args.cmake:
            cmake_lists_path = args.cmake
        convert_project(context, args.project, cmake_lists_path)
    else:
        context['is_converting_solution'] = True
        context['solution_languages'] = set()
        sln = open(args.solution)
        solution_data = parse_solution(sln.read())
        sln.close()

        solution_path = os.path.dirname(args.solution)
        sln_cmake = get_cmake_lists(solution_path)
        DataConverter.add_cmake_version_required(sln_cmake)
        sln_cmake.write('project({0})\n\n'. format(os.path.splitext(os.path.basename(args.solution))[0]))
        subdirectories = []
        for guid in solution_data:
            project_path = solution_data[guid]['path']
            project_path = '/'.join(project_path.split('\\'))
            project_abs = os.path.join(solution_path, project_path)
            subdirectory = os.path.dirname(project_abs)
            set_dependencies_for_project(context, solution_data[guid])
            convert_project(context, project_abs, subdirectory)
            cmake_dir = os.path.dirname(context['cmake'].name)
            subdirectories.append(os.path.relpath(cmake_dir, solution_path))
            print('\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Set target arch type if empty. Visual studio solution generator provides it. #\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('if(NOT CMAKE_VS_PLATFORM_NAME)\n')
        sln_cmake.write('    set(CMAKE_VS_PLATFORM_NAME "x64")\n')
        sln_cmake.write('endif()\n')
        sln_cmake.write('message(\"${CMAKE_VS_PLATFORM_NAME} architecture in use\")\n\n')

        # TODO: try to write configuration types for each project locally due possible difference.
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Global configuration types\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('set(CMAKE_CONFIGURATION_TYPES\n')
        configuration_types_list = list(context['configuration_types'])
        configuration_types_list.sort(key=str.lower)
        for configuration_type in configuration_types_list:
            sln_cmake.write('    \"{0}\"\n'.format(configuration_type))
        sln_cmake.write('    CACHE TYPE INTERNAL FORCE\n)\n\n')

        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Global compiler options\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('if(MSVC)\n')
        sln_cmake.write('  # remove default flags provided with CMake for MSVC\n')
        solution_languages = list(context['solution_languages'])
        solution_languages.sort(key=str.lower)
        for lang in solution_languages:
            sln_cmake.write('  set(CMAKE_{0}_FLAGS "")\n'.format(lang))
            for configuration_type in configuration_types_list:
                sln_cmake.write('  set(CMAKE_{0}_FLAGS_{1} "")\n'.format(lang, configuration_type.upper()))
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
        for configuration_type in configuration_types_list:
            ct_upper = configuration_type.upper()
            sln_cmake.write(
                '  set(CMAKE_EXE_LINKER_FLAGS_{0} \"${{CMAKE_EXE_LINKER_FLAGS}}\")\n'.format(ct_upper))
            sln_cmake.write(
                '  set(CMAKE_MODULE_LINKER_FLAGS_{0} \"${{CMAKE_MODULE_LINKER_FLAGS}}\")\n'.format(ct_upper))
            sln_cmake.write(
                '  set(CMAKE_SHARED_LINKER_FLAGS_{0} \"${{CMAKE_SHARED_LINKER_FLAGS}}\")\n'.format(ct_upper))
            sln_cmake.write(
                '  set(CMAKE_STATIC_LINKER_FLAGS_{0} \"${{CMAKE_STATIC_LINKER_FLAGS}}\")\n'.format(ct_upper))
        sln_cmake.write('endif()\n\n')

        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Nuget packages function stub.\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('function(use_package TARGET PACKAGE)\n')
        sln_cmake.write('    message(WARNING "No implementation of use_package. Create yours.")\n')
        sln_cmake.write('endfunction()\n\n')

        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Additional Global Settings(add specific info there)\n')
        sln_cmake.write('################################################################################\n')
        sln_cmake.write('include(CMake/GlobalSettingsInclude.cmake)\n\n')

        sln_cmake.write('################################################################################\n')
        sln_cmake.write('# Sub-projects\n')
        sln_cmake.write('################################################################################\n')
        subdirectories.sort(key=str.lower)
        for subdirectory in subdirectories:
            sln_cmake.write('add_subdirectory({0})\n'.format(set_unix_slash(subdirectory)))
        sln_cmake.write('\n')
        sln_cmake.close()


if __name__ == "__main__":  # pragma: no cover
    main()
