#!/usr/bin/env python
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

import os
import unittest

from cmake_converter.context import Context
from cmake_converter.data_converter import DataConverter
from cmake_converter.visual_studio.vcxproj.context import VCXContextInitializer


class TestDependencies(unittest.TestCase):
    """
        This file test methods of Dependencies class.
    """

    def setUp(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        context = Context()
        context.silent = True
        vs_project = '{}/datatest/foo.vcxproj'.format(cur_dir)
        VCXContextInitializer(context, vs_project, cur_dir)
        context.cmake = './'
        converter = DataConverter()
        converter.convert(context)

    def test_write_include_dir(self):
        """Write Include Dirs"""

        with open('CMakeLists.txt') as cmake_lists_test:
            cmake_content = cmake_lists_test.read()
            self.assertTrue(
                '${CMAKE_CURRENT_SOURCE_DIR}/../../../external/g3log/latest/src' in cmake_content
            )

    def test_write_dependencies(self):
        """Write Dependencies"""

        with open('CMakeLists.txt') as cmake_lists_test:
            content_test = cmake_lists_test.read()
            self.assertTrue('add_dependencies(${PROJECT_NAME} g3log zlib)' in content_test)
            # self.assertTrue('link_directories(${DEPENDENCIES_DIR}/g3log)' in content_test)

    def test_link_dependencies(self):
        """Link Dependencies"""

        with open('CMakeLists.txt') as cmake_lists_test:
            self.assertTrue('target_link_libraries(${PROJECT_NAME} g3log zlib)'
                            in cmake_lists_test.read())
