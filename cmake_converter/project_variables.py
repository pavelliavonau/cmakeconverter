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
    ProjectVariables
    ================
     Manage creation of CMake variables that will be used during compilation
"""

from cmake_converter.data_files import get_propertygroup
from cmake_converter.utils import get_configuration_type, write_property_of_settings
from cmake_converter.utils import cleaning_output, message


class ProjectVariables(object):
    """
        Class who manage project variables
    """

    def __init__(self, context):
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.output = context['cmake_output']
        self.project_name = context['project_name']
        self.settings = context['settings']
        self.context = context

    def add_project_variables(self, cmake_file):
        """
        Add main CMake project variables

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if not self.project_name == '':
            cmake_file.write('set(PROJECT_NAME ' + self.project_name + ')\n')
        else:
            cmake_file.write('set(PROJECT_NAME <PLEASE SET YOUR PROJECT NAME !!>)\n')
            message(
                'No PROJECT NAME found or define. '
                'Please set [PROJECT_NAME] variable in CMakeLists.txt.',
                'error'
            )

    @staticmethod
    def add_default_target(cmake_file):
        """
        Add default target release if not define

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        cmake_file.write(
            '# Define Release by default.\n'
            'if(NOT CMAKE_BUILD_TYPE)\n'
            '  set(CMAKE_BUILD_TYPE "Release")\n'
            '  message(STATUS "Build type not specified: Use Release by default.")\n'
            'endif(NOT CMAKE_BUILD_TYPE)\n\n'
        )

    def write_target_outputs(self, context, cmake_file):
        """
        Add outputs for each artefacts CMake target

        :param context: related full context
        :type context: dict
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(context['settings']) == 0:
            return

        write_property_of_settings(
            cmake_file, self.settings,
            self.context['sln_configurations_map'],
            'string(CONCAT OUT_DIR', ')', 'out_dir', '',
            '${CMAKE_SOURCE_DIR}/${CMAKE_VS_PLATFORM_NAME}/$<CONFIG>'
        )

        for setting in self.settings:
            break

        if 'vfproj' in context['vcxproj_path']:
            configuration_type = 'StaticLibrary'
        else:
            configuration_type = get_configuration_type(setting, context)

        if configuration_type:
            left_string = 'set_target_properties(${PROJECT_NAME} PROPERTIES '
            right_string = '_OUTPUT_DIRECTORY ${OUT_DIR})\n'
            if configuration_type == 'DynamicLibrary' or configuration_type == 'StaticLibrary':
                cmake_file.write(
                    left_string + 'ARCHIVE' + right_string)
                if configuration_type == 'DynamicLibrary':
                    cmake_file.write(left_string + 'RUNTIME' + right_string)
                # TODO: do we really need LIBRARY_OUTPUT_DIRECTORY here?
                cmake_file.write(left_string + 'LIBRARY' + right_string)
                cmake_file.write('\n')
            else:
                cmake_file.write(
                    left_string + 'RUNTIME' + right_string + '\n')

        write_property_of_settings(
            cmake_file, self.settings,
            self.context['sln_configurations_map'],
            'string(CONCAT TARGET_NAME', ')', 'output_name', '',
            '${PROJECT_NAME}'
        )
        cmake_file.write(
            'set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME ${TARGET_NAME})\n\n'
        )


class VCXProjectVariables(ProjectVariables):
    """
        Class who defines all the CMake variables to be used by the C/C++ project
    """

    def __init__(self, context):
        ProjectVariables.__init__(self, context)
        self.vs_outputs = {}

    def find_outputs_variables(self):
        """
        Add Outputs Variables

        """

        for setting in self.settings:
            prop = get_propertygroup(setting)
            conf = self.settings[setting]['conf']
            arch = self.settings[setting]['arch']
            if conf not in self.vs_outputs:
                self.vs_outputs[conf] = {}
            if arch not in self.vs_outputs[conf]:
                self.vs_outputs[conf][arch] = None

            if not self.vs_outputs[conf][arch]:
                self.vs_outputs[conf][arch] = self.tree.find(
                    '%s/ns:OutDir' % prop, namespaces=self.ns
                )
                if self.vs_outputs[conf][arch] is None:
                    vs_output = self.tree.xpath(
                        '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns)
                    if vs_output:
                        self.vs_outputs[conf][arch] = vs_output[0]
                if self.vs_outputs[conf][arch] is None:
                    vs_output = self.tree.xpath(
                        '//ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"]'
                        .format(setting), namespaces=self.ns)
                    if vs_output:
                        self.vs_outputs[conf][arch] = vs_output[0]

            output_name = '$(ProjectName)'  # default
            output_name_node = self.tree.find(
                '{0}/ns:TargetName'.format(prop), namespaces=self.ns
            )
            if output_name_node is not None:
                output_name = output_name_node.text
            self.settings[setting]['output_name'] = cleaning_output(output_name)

        for setting in self.settings:
            conf = self.settings[setting]['conf']
            arch = self.settings[setting]['arch']

            output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

            if not self.output:
                    if self.vs_outputs[conf][arch] is not None:
                        output_path = cleaning_output(self.vs_outputs[conf][arch].text)
                    else:
                        output_path = cleaning_output(output_path)
            else:
                if self.output[-1:] == '/' or self.output[-1:] == '\\':
                    build_type = '${CMAKE_BUILD_TYPE}'
                else:
                    build_type = '/${CMAKE_BUILD_TYPE}'
                output_path = self.output + build_type

            output_path = output_path.strip().replace('\n', '')
            self.settings[setting]['out_dir'] = output_path

            if output_path:
                message('Output {0} = {1}'.format(setting, output_path), '')
            else:  # pragma: no cover
                message('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')


class VFProjectVariables(ProjectVariables):
    """
         Class who defines all the CMake variables to be used by the Fortran project
    """

    def find_outputs_variables(self):
        """
             Add Outputs Variables
        """

        for setting in self.settings:
            arch = self.settings[setting]['arch']

            output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

            if not self.output:
                if 'out_dir' in self.settings[setting]:
                    output_path = cleaning_output(self.settings[setting]['out_dir'])
                else:
                    output_path = cleaning_output(output_path)
            else:
                if self.output[-1:] == '/' or self.output[-1:] == '\\':
                    build_type = '${CMAKE_BUILD_TYPE}'
                else:
                    build_type = '/${CMAKE_BUILD_TYPE}'
                output_path = self.output + build_type

            output_path = output_path.strip().replace('\n', '')
            self.settings[setting]['out_dir'] = output_path

            if output_path:
                message('Output {0} = {1}'.format(setting, output_path), '')
            else:  # pragma: no cover
                message('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')
