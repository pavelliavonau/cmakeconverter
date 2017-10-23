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

"""
    Data Converter manage conversion of vcxproj data
"""

import os

from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists

from cmake_converter.dependencies import Dependencies
from cmake_converter.flags import Flags, define_and_write_macro
from cmake_converter.message import send
from cmake_converter.projectfiles import ProjectFiles
from cmake_converter.projectvariables import ProjectVariables


class DataConverter:
    """
        Class who convert data to CMakeLists.txt.
    """

    def __init__(self, data):
        self.data = data

    def init_files(self, vs_project, cmake_lists):
        """
        Initialize opening of CMake and VS Project files

        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake_lists: CMakeLists.txt file path
        :type cmake_lists: str
        """

        # VS Project (.vcxproj)
        if vs_project:
            temp_path = os.path.splitext(vs_project)
            if temp_path[1] == '.vcxproj':
                send('Project to convert = ' + vs_project, '')
                self.data['vcxproj'] = get_vcxproj_data(vs_project)
            else:
                send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
                exit(1)

        # CMakeLists
        if cmake_lists:
            if os.path.exists(cmake_lists):
                self.data['cmake'] = get_cmake_lists(cmake_lists)

        if not self.data['cmake']:
            send(
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
            self.data['cmake'] = get_cmake_lists()

    def create_data(self):
        """
        Create the data and convert each part of vcxproj project

        """

        # Write variables
        variables = ProjectVariables(self.data)
        variables.define_variable()
        files = ProjectFiles(self.data)
        files.write_files_variables()
        variables.define_project()
        variables.define_target()

        # Write Macro
        define_and_write_macro(self.data)

        # Write Output Variables
        variables.write_output()

        # Write Include Directories
        depends = Dependencies(self.data)
        if self.data['includes']:
            depends.write_include_dir()
        else:
            send('Include Directories is not set.', '')

        # Write Dependencies
        depends.write_dependencies()

        # Add additional code or not
        if self.data['additional_code'] is not None:
            files.add_additional_code(self.data['additional_code'])

        # Write Flags
        all_flags = Flags(self.data)
        all_flags.write_flags()

        # Write and add Files
        files.write_files()
        files.add_artefact()

        # Link with other dependencies
        depends.link_dependencies()

    def close_cmake_file(self):
        """
        Close the CmakeLists.txt file

        """

        self.data['cmake'].close()
