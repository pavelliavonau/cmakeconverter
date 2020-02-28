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
from cmake_converter.data_converter import DataConverter


class TestFlags(unittest.TestCase):
    """
        This file test methods of Flags class.
    """

    def setUp(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        context = VSContext()
        context.verbose = False
        vs_project = '{}/datatest/foo.vcxproj'.format(cur_dir)
        context.cmake = './'
        converter = DataConverter()
        converter.convert_project(context, vs_project, cur_dir)

