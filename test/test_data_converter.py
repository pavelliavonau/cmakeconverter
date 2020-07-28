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

from cmake_converter.data_converter import DataConverter
from cmake_converter.visual_studio.context import VSContext


class TestDataConverter(unittest.TestCase):
    """
        This file test methods of DataConverter class.
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    vs_project = '%s/datatest/foo.vcxproj' % cur_dir

    def test_context_init(self):
        """Data Converter Init Files"""

        under_test = VSContext()

        self.assertEqual(under_test.cmake, '')
        self.assertEqual(under_test.xml_data, {})

        under_test.init(self.vs_project, self.cur_dir)

        self.assertNotEqual(under_test.cmake, '')
        # self.assertIsNotNone(under_test.vcxproj)

        # self.assertTrue('ns' in under_test.vcxproj)
        # self.assertTrue('tree' in under_test.vcxproj)

    def test_create_data(self):
        """Data Converter Create Data"""

        # FIXME: No such file or directory: 'CMakeLists.txt'
        return

        under_test = DataConverter()

        context = VSContext()
        context.init(self.vs_project, self.cur_dir)

        old_cmake = open('CMakeLists.txt', 'r')

        under_test.convert(context)

        new_cmake = open('CMakeLists.txt', 'r')

        # Assert content is not the same after
        self.assertEqual(old_cmake.read(), new_cmake.read())

        old_cmake.close()
        new_cmake.close()

    def test_receive_wrong_cmake_path(self):
        """Wrong CMake Path Write in Current Directory"""

        under_test = VSContext()
        under_test.init(self.vs_project, '/wrong/path/to/cmake')

        # CMakeLists.txt is created in the current directory
        self.assertEqual('CMakeLists.txt', under_test.cmake)

    ''' #TODO: lost feature?
    def test_inclusion_of_cmake_is_written(self):
        """Inclusion of ".cmake" File is Written"""

        data_test = {
            'cmake': './',
            'cmakeoutput': '',
            'vcxproj': self.vs_project,
            'project': self.vs_project,
            'include': '../../test.txt',
            'includecmake': '../../test.cmake',
            'additional': '',
        }
        under_test = DataConverter(data_test)
        under_test.init_files(self.vs_project, '.')
        under_test.data['cmake'] = get_cmake_lists(context, './')

        under_test.create_data()
        under_test.close_cmake_file()

        cmakelists_test = open('CMakeLists.txt')

        content_test = cmakelists_test.read()

        # Includes are added
        self.assertTrue('Include files and directories' in content_test)
        self.assertTrue('../../test.cmake' in content_test)

        # File "test.txt" is not added because it does not exist
        self.assertTrue('../../test.txt' not in content_test)

        cmakelists_test.close()
    '''
