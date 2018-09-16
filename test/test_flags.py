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
from cmake_converter.data_files import get_cmake_lists


class TestFlags(unittest.TestCase):
    """
        This file test methods of Flags class.
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

    @unittest.skip("linux flags not used")
    def test_define_linux_flags_with_std(self):
        """Define Linux Flags"""

        self.data_test['cmake'] = get_cmake_lists(self.context, './')
        self.data_test['std'] = 'c++17'
        under_test = CPPFlags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++17' in content_test)
        cmakelists_test.close()

        self.data_test['cmake'] = get_cmake_lists(context, './')
        self.data_test['std'] = 'c++19'
        under_test = CPPFlags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++11' in content_test)
        cmakelists_test.close()
