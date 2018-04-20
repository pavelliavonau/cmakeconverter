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

from cmake_converter.message import send
from cmake_converter.data_files import get_propertygroup
from cmake_converter.utils import get_configuration_type


class ProjectVariables(object):
    """
        Class who defines all the CMake variables to be used by the project
    """

    def __init__(self, context):
        self.cmake = context['cmake']
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.output = context['cmake_output']
        self.project_name = context['project_name']
        self.settings = context['settings']
        self.vs_outputs = {}

    def add_project_variables(self):
        """
        Add main CMake project variables

        """

        if not self.project_name == '':
            self.cmake.write('set(PROJECT_NAME ' + self.project_name + ')\n')
        else:
            self.cmake.write('set(PROJECT_NAME <PLEASE SET YOUR PROJECT NAME !!>)\n')
            send(
                'No PROJECT NAME found or define. '
                'Please set [PROJECT_NAME] variable in CMakeLists.txt.',
                'error'
            )

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
                    vs_output_debug_x64 = self.tree.xpath(
                        '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns
                    )
                    if vs_output_debug_x64:
                        self.vs_outputs[conf][arch] = vs_output_debug_x64[0]

            output_name = '$(ProjectName)'  # default
            output_name_node = self.tree.find(
                    '{0}/ns:TargetName'.format(prop), namespaces=self.ns)
            if output_name_node is not None:
                output_name = output_name_node.text
            self.settings[setting]['output_name'] = self.cleaning_output(output_name)

    def find_outputs_variables(self):
        """
        Add Outputs Variables

        """

        for setting in self.settings:
            conf = self.settings[setting]['conf']
            arch = self.settings[setting]['arch']

            output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

            if not self.output:
                    if self.vs_outputs[conf][arch] is not None:
                        output_path = self.cleaning_output(self.vs_outputs[conf][arch].text)
                    else:
                        output_path = self.cleaning_output(output_path)
            else:
                if self.output[-1:] == '/' or self.output[-1:] == '\\':
                    build_type = '${CMAKE_BUILD_TYPE}'
                else:
                    build_type = '/${CMAKE_BUILD_TYPE}'
                output_path = self.output + build_type

            output_path = output_path.strip().replace('\n', '')
            self.settings[setting]['out_dir'] = output_path

            if output_path:
                send('Output {0} = {1}'.format(setting, output_path), 'ok')
            else:  # pragma: no cover
                send('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')

    @staticmethod
    def cleaning_output(output):
        """
        Clean Output string by remove VS Project Variables

        :param output: Output to clean
        :type output: str
        :return: clean output
        :rtype: str
        """

        variables_to_replace = {
            '$(SolutionDir)': '${CMAKE_SOURCE_DIR}/',
            '$(Platform)': 'x64',
            '$(Configuration)': '$<CONFIG>',
            '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}',
            '$(ProjectName)': '${PROJECT_NAME}'
            }
        output = output.replace('\\', '/')

        for var in variables_to_replace:
            if var in output:
                output = output.replace(var, variables_to_replace[var])

        if '%s..' % var in output:
            output = output.replace('%s..' % var, '..')

        return output

    def add_default_target(self):
        """
        Add default target release if not define.

        """

        self.cmake.write(
            '# Define Release by default.\n'
            'if(NOT CMAKE_BUILD_TYPE)\n'
            '  set(CMAKE_BUILD_TYPE "Release")\n'
            '  message(STATUS "Build type not specified: Use Release by default.")\n'
            'endif(NOT CMAKE_BUILD_TYPE)\n\n'
        )

    def add_artifact_target_outputs(self, context):
        """
        Add outputs for each artefacts CMake target

        """

        if len(context['settings']) == 0:
            return

        self.cmake.write('\nstring(CONCAT OUT_DIR\n')
        for setting in context['settings']:
            conf = self.settings[setting]['conf']
            out = context['settings'][setting]['out_dir']
            self.cmake.write('    \"$<$<CONFIG:{0}>:{1}>\"\n'.format(conf, out))
        self.cmake.write(')\n')

        configuration_type = get_configuration_type(setting, context)
        if configuration_type == 'DynamicLibrary' or configuration_type == 'StaticLibrary':
            self.cmake.write(
                'set_target_properties(${PROJECT_NAME} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY "${OUT_DIR}")\n')
            if configuration_type == 'DynamicLibrary':
                self.cmake.write(
                    'set_target_properties(${PROJECT_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${OUT_DIR}")\n')
            # TODO: do we really need LIBRARY_OUTPUT_DIRECTORY here?
            self.cmake.write(
                'set_target_properties(${PROJECT_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${OUT_DIR}")\n')
        else:
            self.cmake.write(
                'set_target_properties(${PROJECT_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${OUT_DIR}")\n')

        self.cmake.write('\nstring(CONCAT TARGET_NAME\n')
        for setting in context['settings']:
            conf = self.settings[setting]['conf']
            out = context['settings'][setting]['output_name']
            self.cmake.write('    \"$<$<CONFIG:{0}>:{1}>\"\n'.format(conf, out))
        self.cmake.write(')\n')

        self.cmake.write(
            'set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME ${TARGET_NAME})\n')