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

from cmake_converter.project_files import ProjectFiles
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestProjectFiles(unittest2.TestCase):
    """
        This file test methods of ProjectFiles class.
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

    def test_init_project_files(self):
        """Initialize Project Files"""

        under_test = ProjectFiles(self.data_test)

        self.assertTrue(under_test.tree)
        self.assertTrue(under_test.ns)
        self.assertTrue(under_test.cmake)
        self.assertTrue(under_test.cppfiles)
        self.assertTrue(under_test.headerfiles)

        self.assertFalse(under_test.language)
        self.assertFalse(under_test.sources)
        self.assertFalse(under_test.headers)

    def test_collects_source_files(self):
        """Collects Source Files"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        self.assertFalse(under_test.sources)
        self.assertFalse(under_test.headers)

        under_test.collects_source_files()
        self.data_test['cmake'].close()

        self.assertTrue(under_test.sources)
        self.assertTrue(under_test.headers)

    def test_write_source_files(self):
        """Write Source Files"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        under_test.collects_source_files()
        under_test.write_source_files()

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('source_group("Sources" FILES ${SRC_FILES})' in content_test)
        self.assertTrue('source_group("Headers" FILES ${HEADERS_FILES})' in content_test)

    def test_add_additional_code(self):
        """Add Additional CMake Code"""

        # When file is empty, nothing is added
        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        under_test.add_additional_code('')

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertEqual('', content_test)
        cmakelists_test.close()

        # When file exist, code is added
        under_test.cmake = get_cmake_lists(self.cur_dir)
        under_test.add_additional_code('%s/test_files/additional_code_test.cmake' % self.cur_dir)

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('set(ADD_CODE code)' in content_test)

        cmakelists_test.close()

        # When file does not exist, nothing is added
        under_test.cmake = get_cmake_lists(self.cur_dir)
        under_test.add_additional_code('nofile/additional_code_test.cmake')

        under_test.cmake.close()

        cmakelists_add_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_add_test = cmakelists_add_test.read()

        self.assertEqual('', content_add_test)

        cmakelists_test.close()

    def test_add_artefacts(self):
        """Add Artefact Target"""

        self.data_test['cmake'] = get_cmake_lists(self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        under_test.collects_source_files()
        under_test.add_target_artefact()

        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('add_library(${PROJECT_NAME} SHARED' in content_test)
        self.assertTrue('${SRC_FILES}' in content_test)

        cmakelists_test.close()
