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
    DataConverter
    =============
     Manage conversion of **vcxproj** data
"""

import os

from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists

from cmake_converter.dependencies import Dependencies
from cmake_converter.flags import Flags
from cmake_converter.message import send
from cmake_converter.project_files import ProjectFiles
from cmake_converter.project_variables import ProjectVariables


class DataConverter:
    """
        Class who convert data to CMakeLists.txt.
    """

    def __init__(self, data):
        self.data = data

    def init_files(self, vs_project, cmake_lists):
        """
        Initialize opening of CMakeLists.txt and VS Project files

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
            else:  # pragma: no cover
                send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
                exit(1)

        # Cmake Project (CMakeLists.txt)
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

    @staticmethod
    def add_cmake_version_required(cmake_file):
        """

        :return:
        """
        cmake_file.write('cmake_minimum_required(VERSION 2.8.0 FATAL_ERROR)\n\n')

    def create_data(self):
        """
        Create the data and convert each part of "vcxproj" project

        """

        if not self.data['is_converting_solution']:
            self.add_cmake_version_required(self.data['cmake'])

        # Write variables
        variables = ProjectVariables(self.data)
        variables.add_project_variables()
        # variables.add_outputs_variables() # TODO: remove hard code of configuration names

        files = ProjectFiles(self.data)
        files.collects_source_files()
        files.add_cmake_project(files.language)
        # variables.add_default_target() # TODO: add conversion option to cmd line

        # Write Output Variables
        # variables.add_artifact_target_outputs() # TODO: remove hard code of configuration names

        # Write Include Directories
        dependencies = Dependencies(self.data)
        if self.data['includes']:
            dependencies.write_include_dir()
        else:
            send('Include Directories is not set.', '')

        # Add additional code or not
        if self.data['additional_code'] is not None:
            files.add_additional_code(self.data['additional_code'])

        files.write_header_files()

        if len(files.sources) != 0:
            all_flags = Flags(self.data)
            all_flags.do_precompiled_headers(files)
            all_flags.define_flags()
            # Writing
            all_flags.write_precompiled_headers_macro()
            files.write_source_files()
            all_flags.write_target_artefact()
            all_flags.write_defines_and_flags()

        # Write Dependencies
        dependencies.write_dependencies()

        # Link with other dependencies
        dependencies.link_dependencies()
        dependencies.extentions_targets_dependencies()

    def close_cmake_file(self):
        """
        Close the "CMakeLists.txt" file

        """

        self.data['cmake'].close()
