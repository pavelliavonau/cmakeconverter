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

from message import send


class CMake(object):
    """
    This class create and open CMakeLists.txt file

    """

    def __init__(self):
        self.cmake = None

    def create_cmake(self, cmake_path=None):
        """
        Create CMakeLists.txt file in wanted path

        :param cmake_path: path where CMakeLists.txt should be write
        :type cmake_path: str
        """

        if cmake_path is None:
            send('CMakeLists will be build in current directory.', '')
            self.cmake = open('CMakeLists.txt', 'w')
        else:
            send('CmakeLists.txt will be build in : ' + str(cmake_path), 'warn')
            if cmake_path[-1:] == '/' or cmake_path[-1:] == '\\':
                self.cmake = open(str(cmake_path) + 'CMakeLists.txt', 'w')
            else:
                self.cmake = open(str(cmake_path) + '/CMakeLists.txt', 'w')
