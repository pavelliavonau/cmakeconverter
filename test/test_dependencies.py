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

import os
import unittest2

from cmake_converter.dependencies import Dependencies
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestDependencies(unittest2.TestCase):
    """
        This file test methods of Dependencies class.
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    vs_project = get_vcxproj_data('%s/test_files/project_test.vcxproj' % cur_dir)
    cmake_lists_test = get_cmake_lists('./')

    data_test = {
        'cmake': cmake_lists_test,
        'cmake_output': None,
        'vcxproj': vs_project,
        'dependencies': None,
        'includes': None,
        'additional_code': None,
        'std': None,
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

        cmakelists_test = open('CMakeLists.txt')

        self.assertTrue(
            'include_directories(../../../external/g3log/latest/src)' in cmakelists_test.read()
        )

        cmakelists_test.close()

    def test_write_dependencies(self):
        """Write Dependencies"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.write_dependencies()
        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt')
        content_test = cmakelists_test.read()

        self.assertTrue(
            'add_subdirectory(test_files/cmake-g3log ${CMAKE_BINARY_DIR}/g3log)' in content_test)
        self.assertTrue(
            'add_subdirectory(test_files/cmake-zlib ${CMAKE_BINARY_DIR}/zlib)' in content_test)

        cmakelists_test.close()

        dependencies = ['external/zlib/cmake/', '../../external/g3log/cmake/']
        self.data_test['dependencies'] = dependencies
        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.write_dependencies()
        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt')
        content_test = cmakelists_test.read()

        self.assertTrue(
            'add_subdirectory(external/zlib/cmake/ ${CMAKE_BINARY_DIR}/lib1)' in content_test)
        self.assertTrue(
            'add_subdirectory(../../external/g3log/cmake/ ${CMAKE_BINARY_DIR}/lib2)' in content_test)

        cmakelists_test.close()

    def test_link_dependencies(self):
        """Link Dependencies"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Dependencies(self.data_test)

        under_test.link_dependencies()
        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt')

        self.assertTrue('target_link_libraries(${PROJECT_NAME}' in cmakelists_test.read())

        cmakelists_test.close()
