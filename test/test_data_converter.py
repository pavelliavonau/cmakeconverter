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

from cmake_converter.data_converter import DataConverter


class TestDataConverter(unittest2.TestCase):
    """
        This file test methods of DataConverter class.
    """

    vs_project = 'test/project_test.vcxproj'

    def test_init_files(self):
        """Data Converter Init Files"""

        data_test = {
            'cmake': None,
            'cmake_output': None,
            'vcxproj': None,
            'dependencies': None,
            'includes': None,
            'additional_code': None,
        }

        under_test = DataConverter(data_test)

        self.assertTrue(under_test.data)
        self.assertIsNone(under_test.data['cmake'])
        self.assertIsNone(under_test.data['vcxproj'])

        under_test.init_files(self.vs_project, './')

        self.assertIsNotNone(under_test.data['cmake'])
        self.assertIsNotNone(under_test.data['vcxproj'])

        self.assertTrue('ns' in under_test.data['vcxproj'])
        self.assertTrue('tree' in under_test.data['vcxproj'])

    def test_create_data(self):
        """Data Converter Create Data"""

        data_test = {
            'cmake': None,
            'cmake_output': None,
            'vcxproj': None,
            'dependencies': None,
            'includes': None,
            'additional_code': None,
        }

        under_test = DataConverter(data_test)
        self.assertTrue(under_test.data)

        under_test.init_files(self.vs_project, '')

        old_cmake = open('CMakeLists.txt', 'r')

        under_test.create_data()

        new_cmake = open('CMakeLists.txt', 'r')

        # Assert content is not the same after
        self.assertEqual(old_cmake.read(), new_cmake.read())

        old_cmake.close()
        new_cmake.close()

    def test_close_cmake_file(self):
        """Close CMake File"""

        data_test = {
            'cmake': None,
            'cmake_output': None,
            'vcxproj': None,
            'dependencies': None,
            'includes': None,
            'additional_code': None,
        }
        under_test = DataConverter(data_test)

        under_test.init_files(self.vs_project, '')
        under_test.create_data()

        self.assertFalse(under_test.data['cmake'].closed)

        under_test.close_cmake_file()

        self.assertTrue(under_test.data['cmake'].closed)
