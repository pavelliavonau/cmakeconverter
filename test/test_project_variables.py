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

from cmake_converter.project_variables import ProjectVariables
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestProjectVariables(unittest2.TestCase):
    """
        This file test methods of ProjectVariables class.
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    vcxproj_data_test = get_vcxproj_data('%s/test_files/project_test.vcxproj' % cur_dir)
    cmake_lists_test = get_cmake_lists(cur_dir)

    data_test = {
        'cmake': cmake_lists_test,
        'cmake_output': None,
        'vcxproj': vcxproj_data_test,
        'dependencies': None,
        'includes': None,
        'additional_code': None,
        'std': None,
    }

    def test_init_project_variables(self):
        """Initialize Project Variables"""

        under_test = ProjectVariables(self.data_test)

        self.assertTrue(under_test.tree)
        self.assertTrue(under_test.ns)
        self.assertTrue(under_test.cmake)
        self.assertFalse(under_test.output)
        self.assertIsNotNone(under_test.vs_outputs)

        # Class var are not None due to other tests
        self.assertIsNotNone(under_test.out_deb)
        self.assertIsNotNone(under_test.out_rel)

    def test_add_project_variables(self):
        """Add Project Variables"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectVariables(self.data_test)

        under_test.add_project_variables()

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)' in content_test)
        self.assertTrue('set(PROJECT_NAME core)' in content_test)

        cmakelists_test.close()

    def test_add_outputs_variables(self):
        """Add Outputs Variables"""

        # TODO If NO output is given
        # self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectVariables(self.data_test)
        #
        # under_test.add_project_variables()
        # under_test.add_outputs_variables()
        #
        # self.data_test['cmake'].close()
        #
        # cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        # content_test = cmakelists_test.read()
        #
        # self.assertTrue('OUTPUT_DEBUG ../../../build/vc2017_x64d/bin/', content_test)
        # self.assertTrue('OUTPUT_REL ../../../build/vc2017_x64/bin/' in content_test)
        #
        # cmakelists_test.close()

        # If output is given
        under_test.output = '../output_binaries'
        under_test.cmake = get_cmake_lists(self.cur_dir)
        under_test.add_outputs_variables()

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('OUTPUT_DEBUG ../output_binaries/${CMAKE_BUILD_TYPE}', content_test)
        self.assertTrue('OUTPUT_REL ../output_binaries/${CMAKE_BUILD_TYPE}' in content_test)

        cmakelists_test.close()

    def test_add_cmake_project(self):
        """Add CMake Project"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectVariables(self.data_test)

        # Case CXX language
        under_test.add_cmake_project(['cpp'])

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('project(${PROJECT_NAME} CXX)' in content_test)

        cmakelists_test.close()

        # Case C language
        under_test.cmake = get_cmake_lists(self.cur_dir)
        under_test.add_cmake_project(['c'])

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('project(${PROJECT_NAME} C)' in content_test)

        cmakelists_test.close()

    def test_add_default_target(self):
        """Add Release as Default Target"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectVariables(self.data_test)

        under_test.add_default_target()

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('set(CMAKE_BUILD_TYPE "Release")' in content_test)

        cmakelists_test.close()

    def test_add_artefact_target_outputs(self):
        """Add Artefact Target Outputs"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectVariables(self.data_test)

        under_test.add_artefact_target_outputs()

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue(
            'set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")' in content_test
        )
        self.assertTrue(
            'set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")' in content_test
        )
        self.assertTrue(
            'set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}' in content_test
        )

        self.assertTrue(
            'set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")' in content_test
        )
        self.assertTrue(
            'set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")' in content_test
        )
        self.assertTrue(
            'set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}' in content_test
        )

        cmakelists_test.close()
