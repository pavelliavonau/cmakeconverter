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
from cmake_converter.utils import mkdir

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
        self.main_vcxproj = None
        self.referenced_projs = []

    def init_files(self, vs_project, cmake_path):
        """
        Initialize opening of CMakeLists.txt and VS Project files

        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake_path: CMakeLists.txt file path
        :type cmake_path: str
        """

        # VS Project (.vcxproj)
        self.main_vcxproj = vs_project

        if os.path.splitext(vs_project)[1] == '.vcxproj':
            send('Project to convert = ' + vs_project, '')
            self.data['vcxproj'] = get_vcxproj_data(vs_project)
        else:  # pragma: no cover
            send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
            exit(1)

        # CMake Project (CMakeLists.txt)
        if os.path.exists(cmake_path):
            self.data['cmake'] = get_cmake_lists(cmake_path)

        self.set_referenced_projects()

    def set_referenced_projects(self):
        """
        Define for current project references, to create the corresponding CMakeLists later

        """

        referenced_projs = self.data['vcxproj']['tree'].xpath(
            '//ns:ProjectReference', namespaces=self.data['vcxproj']['ns']
        )

        for ref_proj in referenced_projs:
            vcxproj = ref_proj.get('Include')
            vcxproj = '/'.join(vcxproj.split('\\'))
            vcxproj = os.path.join(os.path.split(self.main_vcxproj)[0], vcxproj)

            cmake_path, proj_name = os.path.split(vcxproj)
            cmake_path = os.path.join(cmake_path, 'cmake-' + proj_name.replace('.vcxproj', ''))
            mkdir(cmake_path)

            self.referenced_projs.append(
                {
                    'vcxproj': vcxproj,
                    'cmake': cmake_path,
                }
            )

    def create_data(self, references=True):
        """
        Create the data and convert each part of "vcxproj" project

        :param references: defines if project had references or not
        :type references: bool
        """

        # Write variables
        variables = ProjectVariables(self.data)
        variables.add_project_variables()
        variables.add_outputs_variables()

        files = ProjectFiles(self.data)
        files.collects_source_files(references=references)
        variables.add_cmake_project(files.language)
        variables.add_default_target()

        # Write Output Variables
        variables.add_artefact_target_outputs()

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

        # Write and add Files
        files.write_source_files()

        if files.sources:
            files.add_target_artefact()
            # Write Flags
            all_flags = Flags(self.data)
            all_flags.define_settings()
            all_flags.write_flags()
            # Write Macro
            all_flags.write_defines_and_flags()

        # depends.write_dependencies2()

        # Link with other dependencies
        depends.link_dependencies()

    def close_cmake_file(self):
        """
        Close the "CMakeLists.txt" file

        """

        self.data['cmake'].close()
