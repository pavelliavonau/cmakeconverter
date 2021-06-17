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
import lxml
import _io

from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists
from cmake_converter.data_files import get_propertygroup, get_definitiongroup
from cmake_converter.visual_studio.context import VSContext


class TestDataFiles(unittest.TestCase):
    """
        This file test 'data_files' functions
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    vs_project = '%s/datatest/foo.vcxproj' % cur_dir

    def test_get_vcxproj_data(self):
        """Get VS Project Data"""

        context = VSContext()
        under_test = get_vcxproj_data(context, self.vs_project)

        self.assertTrue('ns' in under_test)
        self.assertEqual(
            {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'},
            under_test['ns']
        )
        self.assertTrue('tree' in under_test)
        self.assertIsInstance(under_test['tree'], lxml.etree._ElementTree)

    def test_get_propertygroup(self):
        """Get Property Group"""

        under_test = get_propertygroup(('Release', 'x64'), 'and @Label="Configuration"')

        self.assertTrue('PropertyGroup' in under_test)
        self.assertTrue('Release|x64' in under_test)

    def test_get_definitiongroup(self):
        """Get Definition Group"""

        under_test = get_definitiongroup(('Release', 'Win32'))

        self.assertTrue('ItemDefinitionGroup' in under_test)
        self.assertTrue('Release|Win32' in under_test)

    def test_get_cmakelists(self):
        """Get CMakeLists.txt"""

        context = VSContext()
        for under_test in get_cmake_lists(context, './'):
            self.assertTrue(under_test)
            self.assertIsInstance(under_test, _io.TextIOWrapper)
