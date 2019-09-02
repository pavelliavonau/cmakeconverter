#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
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

from cmake_converter.context import Context
from cmake_converter.visual_studio.solution import VSSolutionConverter
from cmake_converter.utils import message


def main():  # pragma: no cover
    """
    Define arguments and message to DataConverter()

    """

    usage = "cmake-converter -s <path/to/file.sln> " \
            "[ -h | -p | -d | -v | -w | -j | -a ]"
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
        help='run converter with given verbocity of warnings([1..4]default=3).',
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

    args = parser.parse_args()

    root_context = Context()
    # Prepare context
    root_context.additional_code = args.additional

    if args.projects_regexp:
        root_context.projects_regexp = args.projects_regexp

    if args.dry:
        root_context.dry = True
        message(root_context, 'Converter runs in dry mode', 'done')

    if args.verbose:
        root_context.verbose = True
        message(root_context, 'Converter runs in verbose mode', 'done')

    if args.jobs:
        root_context.jobs = int(args.jobs)
    message(root_context, 'processes count = {}'. format(root_context.jobs), 'done')

    if args.warn:
        root_context.warn_level = int(args.warn)
    message(root_context, 'warnings level = {}'. format(root_context.warn_level), 'done')

    if args.private_includes:
        message(root_context, 'include directories will be PRIVATE', 'done')
        root_context.private_include_directories = True

    converter = VSSolutionConverter()
    converter.convert_solution(root_context, os.path.abspath(args.solution))


if __name__ == "__main__":  # pragma: no cover
    main()
