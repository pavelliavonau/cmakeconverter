#!/usr/bin/env python
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

import unittest2
import os

from cmake_converter.dependencies import Dependencies
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestDependencies(unittest2.TestCase):
    """
        This file test methods of ActionManager class.
    """

    vcxproj_data_test = get_vcxproj_data('test/project_test.vcxproj')
    cmake_lists_test = get_cmake_lists('./')

    data_test = {
        'cmake': cmake_lists_test,
        'cmake_output': None,
        'vcxproj': vcxproj_data_test,
        'dependencies': None,
        'includes': None,
        'additional_code': None,
    }

    def test_init_dependencies(self):
        """Initialize Dependencies"""

        under_test = Dependencies(self.data_test)

        self.assertTrue(under_test.cmake)
        self.assertTrue(under_test.tree)
        self.assertTrue(under_test.ns)
        self.assertFalse(under_test.dependencies)

    def test_write_include_dir(self):
        """Write Include Dirs"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.write_include_dir()
        self.data_test['cmake'].close()

        new_cmake = open('CMakeLists.txt', 'r')

        self.assertTrue(
            'include_directories(../../../external/g3log/latest/src)' in new_cmake.read()
        )

    def test_write_dependencies(self):
        """Write Dependencies"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.write_dependencies()
        self.data_test['cmake'].close()

        new_cmake = open('CMakeLists.txt', 'r')

        self.assertTrue('Add Dependencies to project. ' in new_cmake.read())

    def test_link_dependencies(self):
        """Link Dependencies"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.link_dependencies()
        self.data_test['cmake'].close()

        new_cmake = open('CMakeLists.txt', 'r')

        self.assertTrue('target_link_libraries(${PROJECT_NAME}' in new_cmake.read())
