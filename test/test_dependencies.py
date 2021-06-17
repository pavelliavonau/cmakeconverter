#!/usr/bin/env python
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

import os
import unittest

from cmake_converter.visual_studio.context import VSContext
from cmake_converter.visual_studio.solution import VSSolutionConverter


class TestDependencies(unittest.TestCase):
    """
        This file test methods of Dependencies class.
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))

    def setUp(self):
        self.context = VSContext()
        self.context.verbose = False
        solution_file = '{}/datatest/sln/cpp.sln'.format(self.cur_dir)
        converter = VSSolutionConverter()
        converter.convert_solution(self.context, os.path.abspath(solution_file))

    def test_write_include_dir(self):
        """Write Include Dirs"""

        with open(self.cur_dir + '/datatest/CMakeLists.txt') as cmake_lists_test:
            cmake_content = cmake_lists_test.read()
            self.assertTrue(
                '${CMAKE_CURRENT_SOURCE_DIR}/external' in cmake_content
            )

    @unittest.skip("add dependency and fix test")
    def test_write_dependencies(self):
        """Write Dependencies"""

        with open(self.cur_dir + '/datatest/CMakeLists.txt') as cmake_lists_test:
            content_test = cmake_lists_test.read()
            self.assertTrue('''add_dependencies(${{PROJECT_NAME}}
{0}g3log
{0}zlib
)'''.format(self.context.indent) in content_test)
            # self.assertTrue('link_directories(${DEPENDENCIES_DIR}/g3log)' in content_test)

    def test_link_dependencies(self):
        """Link Dependencies"""

        with open(self.cur_dir + '/datatest/CMakeLists.txt') as cmake_lists_test:
            self.assertTrue('''target_link_libraries(${{PROJECT_NAME}} PRIVATE
{0}g3log
{0}zlib
)'''.format(self.context.indent) in cmake_lists_test.read())
