#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
#   Matthieu Estrada, ttamalfor@gmail.com
#   Pavel Liavonau, liavonlida@gmail.com
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
import os

from cmake_converter.visual_studio.context import VSContext
from cmake_converter.visual_studio.solution import VSSolutionConverter
from cmake_converter.utils import message


def main():  # pragma: no cover
    """
    Define arguments and message to DataConverter()

    """

    usage = "cmake-converter -s <path/to/file.sln> " \
            "[ -h | -s | -p | -i | -d | -v | -w | -j | -a | -pi | -ias ]"
    parser = argparse.ArgumentParser(
        usage=usage,
        description='Converts Visual Studio projects in solution (*.sln) to CMakeLists.txt tree'
    )
    parser.add_argument(
        '-s', '--solution',
        help='[required] valid solution file. i.e.: ../../my.sln',
        required=True,
        dest='solution'
    )
    parser.add_argument(
        '-p', '--projects-filter',
        help='python regexp to filter that projects should be converted from the given solution',
        dest='projects_regexp'
    )
    parser.add_argument(
        '-i', '--indent',
        help='indentation for formatting of out CMakeLists.txt',
        dest='indent'
    )
    parser.add_argument(
        '-d', '--dry-run',
        help='run converter without touching files.',
        dest='dry',
        action='store_true'
    )
    parser.add_argument(
        '-v', '--verbose-mode',
        help='run converter with more messages in log.',
        dest='verbose',
        action='store_true'
    )
    parser.add_argument(
        '-w', '--warning-level',
        help='run converter with given verbosity of warnings([1..4] default=2).',
        dest='warn',
    )
    parser.add_argument(
        '-j', '--jobs',
        help='run converter using given number of processes.',
        dest='jobs',
    )
    parser.add_argument(
        '-a', '--additional',
        help='[experimental] import cmake code from file.cmake to your final CMakeLists.txt',
        dest='additional'
    )
    parser.add_argument(
        '-pi', '--private-include-directories',
        help='use PRIVATE specifier for target_include_directories',
        dest='private_includes',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '-ias', '--ignore-absent-sources',
        help='do not add absent source files to CMakeLists.txt',
        dest='ignore_absent_sources',
        default=False,
        action='store_true'
    )

    args = parser.parse_args()

    project_context = VSContext()
    # Prepare context
    project_context.additional_code = args.additional

    if args.projects_regexp:
        project_context.projects_regexp = args.projects_regexp

    if args.indent:
        project_context.indent = args.indent

    if args.dry:
        project_context.dry = True
        message(project_context, 'Converter runs in dry mode', 'done')

    if args.verbose:
        project_context.verbose = True
        message(project_context, 'Converter runs in verbose mode', 'done')

    if args.jobs:
        project_context.jobs = int(args.jobs)
    message(project_context, 'processes count = {}'. format(project_context.jobs), 'done')

    if args.warn:
        project_context.warn_level = int(args.warn)
    message(project_context, 'warnings level = {}'. format(project_context.warn_level), 'done')

    if args.private_includes:
        message(project_context, 'include directories will be PRIVATE', 'done')
        project_context.private_include_directories = True

    if args.ignore_absent_sources:
        message(project_context, 'absent source files will be ignored', 'done')
        project_context.ignore_absent_sources = True

    converter = VSSolutionConverter()
    converter.convert_solution(project_context, os.path.abspath(args.solution))


if __name__ == "__main__":  # pragma: no cover
    main()
