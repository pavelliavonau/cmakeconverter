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

import unittest

from cmake_converter.writer import CMakeWriter


class TestUtils(unittest.TestCase):
    """
        This file test methods of utils package
    """

    def test_get_title(self):
        """Get Comment"""

        under_test = CMakeWriter.get_comment('text of comment')

        self.assertEqual(
            '################################################################################\n'
            '# text of comment\n'
            '################################################################################\n',
            under_test
        )


if __name__ == '__main__':
    unittest.main()
