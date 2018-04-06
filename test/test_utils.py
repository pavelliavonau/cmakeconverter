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

from cmake_converter.utils import get_title


class TestUtils(unittest2.TestCase):
    """
        This file test methods of utils package
    """

    def test_get_title(self):
        """Get Title"""

        under_test = get_title('Title', 'text of title')

        self.assertEqual(
            '######################### Title ############################\n'
            '# text of title                                            #\n'
            '############################################################\n\n',
            under_test
        )
