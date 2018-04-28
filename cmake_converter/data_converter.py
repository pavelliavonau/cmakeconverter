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

from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists, get_propertygroup, get_definitiongroup,\
    get_xml_data

from cmake_converter.dependencies import Dependencies
from cmake_converter.flags import CPPFlags, FortranFlags
from cmake_converter.message import send
from cmake_converter.project_files import ProjectFiles
from cmake_converter.project_variables import VCXProjectVariables, VFProjectVariables
from cmake_converter.utils import get_global_project_name_from_vcxproj_file


class DataConverter:
    """
    Base class for converters
    """
    def __init__(self, context):
        self.context = context

    @staticmethod
    def add_cmake_version_required(cmake_file):
        """

        :return:
        """
        cmake_file.write('cmake_minimum_required(VERSION 2.8.0 FATAL_ERROR)\n\n')

    def close_cmake_file(self):
        """
        Close the "CMakeLists.txt" file

        """

        self.context['cmake'].close()


class CPPConverter(DataConverter):
    """
        Class who convert data to CMakeLists.txt.
    """

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
            project_name = os.path.basename(temp_path[0])
            if temp_path[1] == '.vcxproj':
                send('Project to convert = ' + vs_project, '')
                self.context['vcxproj'] = get_vcxproj_data(vs_project)
                self.context['vcxproj_path'] = vs_project
                project_name_value = get_global_project_name_from_vcxproj_file(self.context['vcxproj'])
                if project_name_value:
                    project_name = project_name_value
                self.context['project_name'] = project_name
            else:  # pragma: no cover
                send('This file is not a ".vcxproj". Be sure you give the right file', 'error')
                exit(1)

        # Cmake Project (CMakeLists.txt)
        if cmake_lists:
            if os.path.exists(cmake_lists):
                cmake = get_cmake_lists(cmake_lists, 'r')
                if cmake:
                    file_text = cmake.read()
                    cmake.close()
                    if 'PROJECT_NAME {0}'.format(project_name) in file_text:
                        self.context['cmake'] = get_cmake_lists(cmake_lists)  # updating
                    else:
                        directory = cmake_lists + '/{0}_cmakelists'.format(project_name)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        self.context['cmake'] = get_cmake_lists(directory)
                else:
                    self.context['cmake'] = get_cmake_lists(cmake_lists)  # writing first time

        if not self.context['cmake']:
            send(
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
            self.context['cmake'] = get_cmake_lists()

    @staticmethod
    def define_settings(context):
        """
        Define the settings of vcxproj

        """

        settings = {}
        property_groups = {}
        definition_groups = {}
        tree = context['vcxproj']['tree']
        ns = context['vcxproj']['ns']
        configuration_nodes = tree.xpath('//ns:ProjectConfiguration', namespaces=ns)
        if configuration_nodes:
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Include'))
                conf_arch = configuration_data.split('|')
                conf = conf_arch[0]
                arch = conf_arch[1]
                settings[configuration_data] = {'defines': [],
                                                'cl_flags': '',
                                                'ln_flags': '',
                                                'conf': conf,
                                                'arch': arch,
                                                }

        for setting in settings:
            property_groups[setting] = get_propertygroup(
                setting, ' and @Label="Configuration"')

        # ItemDefinitionGroup
        for setting in settings:
            definition_groups[setting] = get_definitiongroup(setting)

        context['settings'] = settings
        context['property_groups'] = property_groups
        context['definition_groups'] = definition_groups

    def create_data(self):
        """
        Create the data and convert each part of "vcxproj" project

        """

        if not self.context['is_converting_solution']:
            self.add_cmake_version_required(self.context['cmake'])

        self.define_settings(self.context)
        # Write variables
        variables = VCXProjectVariables(self.context)
        variables.add_project_variables()
        variables.find_outputs_variables()

        files = ProjectFiles(self.context)
        files.collects_source_files()
        files.add_cmake_project(files.language)
        # variables.add_default_target() # TODO: add conversion option to cmd line

        # Add additional code or not
        if self.context['additional_code'] is not None:
            files.add_additional_code(self.context['additional_code'])

        files.write_header_files()

        if len(files.sources) != 0:
            all_flags = CPPFlags(self.context)
            all_flags.do_precompiled_headers(files)
            all_flags.define_flags()
            # Writing
            all_flags.write_precompiled_headers_macro()
            files.write_source_files()
            all_flags.write_target_artifact()
            variables.add_artifact_target_outputs(self.context)
            dependencies = Dependencies(self.context)
            dependencies.write_include_dir()
            all_flags.write_defines_and_flags()
            for configuration_type in all_flags.get_cmake_configuration_types():
                self.context['configuration_types'].add(configuration_type)

            # Write Dependencies
            dependencies.write_dependencies()

            # Link with other dependencies
            dependencies.link_dependencies()
            dependencies.extensions_targets_dependencies()


class FortranProjectConverter(DataConverter):
    """
        Class who convert Fortran project to CMakeLists.txt.
    """

    def init_files(self, vf_project, cmake_lists):
        """
        Initialize opening of CMakeLists.txt and VS Project files

        :param vf_project: Visual Studio project file path
        :type vf_project: str
        :param cmake_lists: CMakeLists.txt file path
        :type cmake_lists: str
        """

        # VS Project (.vfproj)
        if vf_project:
            temp_path = os.path.splitext(vf_project)
            project_name = os.path.basename(temp_path[0])
            if temp_path[1] == '.vfproj':
                send('Project to convert = ' + vf_project, '')
                self.context['vcxproj'] = get_xml_data(vf_project)
                self.context['vcxproj_path'] = vf_project
                self.context['project_name'] = project_name
            else:  # pragma: no cover
                send('This file is not a ".vfproj". Be sure you give the right file', 'error')
                exit(1)

        # Cmake Project (CMakeLists.txt)
        if cmake_lists:
            if os.path.exists(cmake_lists):
                cmake = get_cmake_lists(cmake_lists, 'r')
                if cmake:
                    file_text = cmake.read()
                    cmake.close()
                    if 'PROJECT_NAME {0}'.format(project_name) in file_text:
                        self.context['cmake'] = get_cmake_lists(cmake_lists)  # updating
                    else:
                        directory = cmake_lists + '/{0}_cmakelists'.format(project_name)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        self.context['cmake'] = get_cmake_lists(directory)
                else:
                    self.context['cmake'] = get_cmake_lists(cmake_lists)  # writing first time

        if not self.context['cmake']:
            send(
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
            self.context['cmake'] = get_cmake_lists()

    @staticmethod
    def define_settings(context):
        """
        Define the settings of vcxproj

        """

        settings = {}
        tree = context['vcxproj']['tree']
        configuration_nodes = tree.xpath('/VisualStudioProject/Configurations/Configuration')
        if configuration_nodes:
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Name'))
                conf_arch = configuration_data.split('|')
                conf = conf_arch[0]
                arch = conf_arch[1]
                settings[configuration_data] = {'defines': [],
                                                'cl_flags': [],
                                                'ln_flags': '',
                                                'conf': conf,
                                                'arch': arch,
                                                }

                out_dir_node = configuration_node.get('OutputDirectory')
                if out_dir_node:
                    settings[configuration_data]['out_dir'] = out_dir_node

                target_name_node = configuration_node.get('TargetName')
                if target_name_node:
                    settings[configuration_data]['output_name'] = target_name_node

                tools = configuration_node.xpath('Tool')
                for tool in tools:
                    tool_name = str(tool.get('Name'))
                    settings[configuration_data][tool_name] = tool.attrib
                    if 'VFFortranCompilerTool' in tool_name:
                        if 'PreprocessorDefinitions' in tool.attrib:
                            settings[configuration_data]['defines'] = tool.attrib['PreprocessorDefinitions'].split(';')

        context['settings'] = settings

    def create_data(self):
        """
        Create the data and convert each part of "vcxproj" project

        """

        if not self.context['is_converting_solution']:
            self.add_cmake_version_required(self.context['cmake'])

        self.define_settings(self.context)
        # Write variables
        variables = VFProjectVariables(self.context)
        variables.add_project_variables()
        variables.find_outputs_variables()

        files = ProjectFiles(self.context)
        files.collects_source_files()
        files.add_cmake_project(files.language)
        # Add additional code or not
        if self.context['additional_code'] is not None:
            files.add_additional_code(self.context['additional_code'])

        files.write_header_files()

        if len(files.sources) != 0:
            all_flags = FortranFlags(self.context)
            all_flags.define_flags()
            # Writing
            files.write_source_files()
            all_flags.write_target_artifact()
            variables.add_artifact_target_outputs(self.context)
            all_flags.write_defines_and_flags()

