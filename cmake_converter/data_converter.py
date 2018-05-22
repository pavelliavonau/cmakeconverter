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
     Manage conversion of **.*proj** data
"""

import os

from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists, get_propertygroup, get_definitiongroup,\
    get_xml_data

from cmake_converter.dependencies import Dependencies
from cmake_converter.flags import CPPFlags, FortranFlags
from cmake_converter.project_files import ProjectFiles
from cmake_converter.project_variables import VCXProjectVariables, VFProjectVariables
from cmake_converter.utils import message
import cmake_converter.utils


class DataConverter:
    """
    Base class for converters
    """
    def __init__(self, context, vs_project, cmake_lists_destination_path):
        self.context = context
        self.init_files(vs_project, cmake_lists_destination_path)
        self.define_settings()

    def define_settings(self):
        raise NotImplementedError('You need to define a define_settings method!')

    def init_context(self, vs_project):
        pass

    def init_context_setting(self, configuration_data):
        conf_arch = configuration_data.split('|')
        conf = conf_arch[0]
        arch = conf_arch[1]
        self.context['settings'][configuration_data] = {'defines': [],
                                                        'cl_flags': [],
                                                        'ln_flags': [],
                                                        'conf': conf,
                                                        'arch': arch,
                                                        }

    def init_files(self, vs_project, cmake_lists):
        """
        Initialize opening of CMakeLists.txt and VS Project files

        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake_lists: CMakeLists.txt file path
        :type cmake_lists: str
        """

        if vs_project:
            temp_path = os.path.splitext(vs_project)
            project_name = os.path.basename(temp_path[0])
            message('Project to convert = ' + vs_project, '')
            self.context['project_name'] = project_name
            self.context['vcxproj_path'] = vs_project
            self.init_context(vs_project)
            self.get_cmake_lists_name(cmake_lists, self.context['project_name'])

    def collect_data(self):
        raise NotImplementedError('You need to define a collect_data method!')

    def write_data(self, cmake_file):
        raise NotImplementedError('You need to define a write_data method!')

    def convert(self):
        """
         Template method
        """
        self.collect_data()
        cmake_file = get_cmake_lists(self.context['cmake'])
        self.write_data(cmake_file)
        cmake_file.close()

    @staticmethod
    def add_cmake_version_required(cmake_file):
        cmake_file.write('cmake_minimum_required(VERSION 2.8.0 FATAL_ERROR)\n\n')

    def get_cmake_lists_name(self, cmake_lists, project_name):
        # Cmake Project (CMakeLists.txt)
        if cmake_lists:
            if os.path.exists(cmake_lists):
                cmake = get_cmake_lists(cmake_lists, 'r')
                cmake_converter.utils.path_prefix = ''
                if cmake:
                    file_text = cmake.read()
                    cmake.close()
                    if 'PROJECT_NAME {0}'.format(project_name) in file_text:
                        self.context['cmake'] = cmake_lists  # updating
                    else:
                        directory = cmake_lists + '/{0}_cmakelists'.format(project_name)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        self.context['cmake'] = directory
                        cmake_converter.utils.path_prefix = '../'
                        message('CMakeLists will be written at subdirectory.', 'warn')
                else:
                    self.context['cmake'] = get_cmake_lists(cmake_lists)  # writing first time

        if not self.context['cmake']:
            message(
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
            self.context['cmake'] = get_cmake_lists()


class VCXProjectConverter(DataConverter):
    """
        Class that converts C++ project to CMakeLists.txt.
    """

    def __init__(self, context, xml_project_path, cmake_lists_destination_path):
        DataConverter.__init__(self, context, xml_project_path, cmake_lists_destination_path)
        self.variables = VCXProjectVariables(self.context)
        self.files = ProjectFiles(self.context)
        self.flags = CPPFlags(self.context)
        self.dependencies = Dependencies(self.context)

    def init_context(self, vs_project):
        project_name = self.context['project_name']
        self.context['vcxproj'] = get_vcxproj_data(vs_project)
        project_name_value = \
            cmake_converter.utils.get_global_project_name_from_vcxproj_file(self.context['vcxproj'])
        if project_name_value:
            project_name = project_name_value
        self.context['project_name'] = project_name

    def define_settings(self):
        """
        Define the settings of vcxproj

        """

        tree = self.context['vcxproj']['tree']
        ns = self.context['vcxproj']['ns']
        configuration_nodes = tree.xpath('//ns:ProjectConfiguration', namespaces=ns)
        if configuration_nodes:
            self.context['settings'] = {}
            self.context['property_groups'] = {}
            self.context['definition_groups'] = {}
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Include'))
                self.init_context_setting(configuration_data)
                self.context['property_groups'][configuration_data] = get_propertygroup(configuration_data,
                                                                                        ' and @Label="Configuration"')
                self.context['definition_groups'][configuration_data] = get_definitiongroup(configuration_data)

    def collect_data(self):
        """
        Collect the data of each part of "vcxproj" project

        """

        self.variables.find_outputs_variables()
        self.files.collects_source_files()
        self.files.find_cmake_project_language()
        if not self.context['has_only_headers']:
            self.flags.do_precompiled_headers(self.files)
            self.flags.define_flags()
            self.dependencies.find_include_dir()
            self.dependencies.find_target_references()
            self.dependencies.find_target_additional_dependencies()
            self.dependencies.find_target_additional_library_directories()
            self.dependencies.find_target_property_sheets()
            self.dependencies.find_target_dependency_packages()

    def write_data(self, cmake_file):
        """
        Write the data of each part of "vcxproj" project into CMakeLists.txt

        """

        if not self.context['is_converting_solution']:
            self.add_cmake_version_required(self.context['cmake'])

        self.variables.add_project_variables(cmake_file)
        self.files.write_cmake_project(cmake_file)
        # self.variables.add_default_target() # TODO: add conversion option to cmd line

        # Add additional code or not
        if self.context['additional_code'] is not None:
            self.files.add_additional_code(self.context['additional_code'], cmake_file)

        self.files.write_header_files(cmake_file)

        if not self.context['has_only_headers']:
            self.flags.write_precompiled_headers_macro(cmake_file)
            self.files.write_source_files(cmake_file)
            self.dependencies.write_target_property_sheets(cmake_file)
            self.flags.write_target_artifact(cmake_file)
            self.variables.write_target_outputs(self.context, cmake_file)
            self.dependencies.write_include_directories(self.context, cmake_file)
            self.flags.write_defines_and_flags('MSVC', cmake_file)
            self.dependencies.write_dependencies(cmake_file)
            self.dependencies.write_link_dependencies(cmake_file)
            self.dependencies.write_target_dependency_packages(cmake_file)
        else:
            CPPFlags.write_target_headers_only_artifact(self.context, cmake_file)


class VFProjectConverter(DataConverter):
    """
        Class that converts Fortran project to CMakeLists.txt.
    """

    def __init__(self, context, xml_project_path, cmake_lists_destination_path):
        DataConverter.__init__(self, context, xml_project_path, cmake_lists_destination_path)
        self.variables = VFProjectVariables(self.context)
        self.files = ProjectFiles(self.context)
        self.flags = FortranFlags(self.context)

    def init_context(self, vs_project):
        self.context['vcxproj'] = get_xml_data(vs_project)

    def define_settings(self):
        """
        Define the settings of vfproj

        """

        tree = self.context['vcxproj']['tree']
        configuration_nodes = tree.xpath('/VisualStudioProject/Configurations/Configuration')
        if configuration_nodes:
            self.context['settings'] = {}
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Name'))
                self.init_context_setting(configuration_data)

                out_dir_node = configuration_node.get('OutputDirectory')
                if out_dir_node:
                    self.context['settings'][configuration_data]['out_dir'] = out_dir_node

                target_name_node = configuration_node.get('TargetName')
                if target_name_node:
                    self.context['settings'][configuration_data]['output_name'] = target_name_node
                else:
                    self.context['settings'][configuration_data]['output_name'] = self.context['project_name']

                tools = configuration_node.xpath('Tool')
                for tool in tools:
                    tool_name = str(tool.get('Name'))
                    self.context['settings'][configuration_data][tool_name] = tool.attrib
                    if 'VFFortranCompilerTool' in tool_name:
                        if 'PreprocessorDefinitions' in tool.attrib:
                            self.context['settings'][configuration_data]['defines'] = tool.attrib['PreprocessorDefinitions']\
                                .split(';')

    def collect_data(self):
        """
        Create the data and convert each part of "vfproj" project

        """

        self.variables.find_outputs_variables()

        self.files.collects_source_files()
        self.files.find_cmake_project_language()

        if not self.context['has_only_headers']:
            self.flags.define_flags()
            for setting in self.context['settings']:
                ad_inc = self.context['settings'][setting]['VFFortranCompilerTool'].get('AdditionalIncludeDirectories')
                if ad_inc:
                    Dependencies.get_additional_include_directories(ad_inc, setting, self.context)
                if 'inc_dirs' in self.context['settings'][setting]:
                    self.context['settings'][setting]['inc_dirs'] += ';${CMAKE_CURRENT_SOURCE_DIR}/'
                else:
                    self.context['settings'][setting]['inc_dirs'] = '${CMAKE_CURRENT_SOURCE_DIR}/'

    def write_data(self, cmake_file):
        if not self.context['is_converting_solution']:
            self.add_cmake_version_required(self.context['cmake'])

        self.variables.add_project_variables(cmake_file)
        self.files.write_cmake_project(cmake_file)
        # Add additional code or not
        if self.context['additional_code'] is not None:
            self.files.add_additional_code(self.context['additional_code'], cmake_file)
        self.files.write_header_files(cmake_file)
        if not self.context['has_only_headers']:
            # Writing
            self.files.write_source_files(cmake_file)
            self.flags.write_target_artifact(cmake_file)
            self.variables.write_target_outputs(self.context, cmake_file)
            Dependencies.write_include_directories(self.context, cmake_file)
            self.flags.write_defines_and_flags('${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"', cmake_file)
