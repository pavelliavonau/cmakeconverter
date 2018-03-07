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

from cmake_converter.flags import Flags
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestFlags(unittest2.TestCase):
    """
        This file test methods of Flags class.
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

    def test_define_linux_flags_with_std(self):
        """Define Linux Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        self.data_test['std'] = 'c++17'
        under_test = Flags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++17' in content_test)
        cmakelists_test.close()

        self.data_test['cmake'] = get_cmake_lists('./')
        self.data_test['std'] = 'c++19'
        under_test = Flags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++11' in content_test)
        cmakelists_test.close()

    def test_define_group_properties(self):
        """Define XML Groups Properties"""

        under_test = Flags(self.data_test)

        self.assertFalse(under_test.propertygroup)
        self.assertFalse(under_test.definitiongroups)

        under_test.define_settings()
        under_test.define_group_properties()

        self.assertTrue(under_test.propertygroup)
        self.assertTrue(under_test.definitiongroups)
