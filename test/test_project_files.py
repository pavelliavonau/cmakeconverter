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
from cmake_converter.project_files import ProjectFiles
from cmake_converter.data_files import get_cmake_lists


class TestProjectFiles(unittest.TestCase):
    """
        This file test methods of ProjectFiles class.
    """

    context = VSContext()
    cur_dir = os.path.dirname(os.path.realpath(__file__))

    def setUp(self):
        self.context.verbose = False
        solution_file = '{}/datatest/sln/cpp.sln'.format(self.cur_dir)
        converter = VSSolutionConverter()
        converter.convert_solution(self.context, os.path.abspath(solution_file))

    @unittest.skip("how to test sources from project context?")
    def test_collects_source_files(self):
        """Collects Source Files"""

        self.assertNotEqual(len(self.context.sources), 0)
        self.assertEqual(len(self.context.headers), 0)

    def test_write_source_files(self):
        """Write Source Files"""

        with open('{}/datatest/CMakeLists.txt'.format(self.cur_dir)) as cmake_lists_test:
            content_test = cmake_lists_test.read()
            self.assertTrue('source_group("Sources" FILES ${Sources})' in content_test)

    @unittest.skip("repair test additional code")
    def test_add_additional_code(self):
        """Add Additional CMake Code"""

        # When file is empty, nothing is added
        self.data_test['cmake'] = get_cmake_lists(context, self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        under_test.add_additional_code(context, '')

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertEqual('', content_test)
        cmakelists_test.close()

        # When file exist, code is added
        under_test.cmake = get_cmake_lists(context, self.cur_dir)
        under_test.add_additional_code(context, '%s/datatest/additional_code_test.cmake' % self.cur_dir)

        under_test.cmake.close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('set(ADD_CODE code)' in content_test)

        cmakelists_test.close()

        # When file does not exist, nothing is added
        under_test.cmake = get_cmake_lists(context, self.cur_dir)
        under_test.add_additional_code(context, 'nofile/additional_code_test.cmake')

        under_test.cmake.close()

        cmakelists_add_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_add_test = cmakelists_add_test.read()

        self.assertEqual('', content_add_test)

        cmakelists_test.close()

    def test_add_artefacts(self):
        """Add Artefact Target"""

        with open('{}/datatest/CMakeLists.txt'.format(self.cur_dir)) as cmake_lists_test:
            content_test = cmake_lists_test.read()
            self.assertTrue('add_executable(${PROJECT_NAME} ${ALL_FILES})' in content_test)

    @unittest.skip("include_cmake deleted")
    def test_add_include_cmake(self):
        """Add Include CMake File"""

        self.data_test['cmake'] = get_cmake_lists(context, self.cur_dir)
        under_test = ProjectFiles(self.data_test)

        under_test.add_include_cmake('path/to/file.cmake')
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir)
        content_test = cmakelists_test.read()

        self.assertTrue('include("path/to/file.cmake")' in content_test)
