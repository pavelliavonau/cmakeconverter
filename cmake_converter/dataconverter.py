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

from cmake_converter.vsproject import VSProject
from cmake_converter.cmakelists import CMakeLists

from cmake_converter.dependencies import Dependencies
from cmake_converter.flags import Flags
from cmake_converter.macro import Macro
from cmake_converter.message import send
from cmake_converter.projectfiles import ProjectFiles
from cmake_converter.projectvariables import ProjectVariables


class DataConverter:
    """
        Class who convert data to CMakeLists.txt.
    """

    def __init__(self, data=None):
        self.data = data

    def init_files(self, vs_project, cmake):
        """
        Initialize opening of CMake and VS Project files

        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake: CMakeLists.txt file path
        :type cmake: str
        """

        # VS Project (.vcxproj)
        if vs_project:
            temp_path = os.path.splitext(vs_project)
            if temp_path[1] == '.vcxproj':
                send('Project to convert = ' + vs_project, '')
                project = VSProject()
                self.data['vcxproj'] = project.create_data(vs_project)
            else:
                send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
                exit(1)

        # CMake Project (CMakeLists.txt)
        if cmake:
            cmakelists = CMakeLists()
            print(cmake)
            if os.path.exists(cmake):
                cmakelists.create_file(cmake)
                self.data['cmake'] = cmakelists.cmake
            else:
                send(
                    'This path does not exist. '
                    'CMakeList.txt will be generated in current directory.',
                    'error'
                )
                cmakelists.create_file()
            self.data['cmake'] = cmakelists.cmake
        else:
            cmakelists = CMakeLists()
            cmakelists.create_file()
            self.data['cmake'] = cmakelists.cmake

    def create_data(self):
        """
        Create the data and convert each part of vcxproj project

        """

        # Write variables
        variables = ProjectVariables(self.data)
        variables.define_variable()
        files = ProjectFiles(self.data)
        files.write_variables()
        variables.define_project()
        variables.define_target()

        # Write Macro
        macros = Macro()
        macros.write_macro(self.data)

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

        # Close CMake file
        self.data['cmake'].close()
