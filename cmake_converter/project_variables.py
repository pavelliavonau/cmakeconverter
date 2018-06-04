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
from cmake_converter.utils import cleaning_output, message, write_comment


class ProjectVariables(object):
    """
        Class who manage project variables
    """

    @staticmethod
    def add_project_variables(context, cmake_file):
        """
        Add main CMake project variables

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if not context.project_name == '':
            cmake_file.write('set(PROJECT_NAME ' + context.project_name + ')\n')
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

    @staticmethod
    def write_target_outputs(context, cmake_file):
        """
        Add outputs for each artefacts CMake target

        :param context: related full context
        :type context: dict
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(context.settings) == 0:
            return

        write_comment(cmake_file, 'Output directory')

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            'string(CONCAT OUT_DIR', ')', 'out_dir', '',
            '${CMAKE_SOURCE_DIR}/${CMAKE_VS_PLATFORM_NAME}/$<CONFIG>'
        )

        for setting in context.settings:
            break

        if 'vfproj' in context.vcxproj_path:
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

        write_comment(cmake_file, 'Target name')
        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
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

    @staticmethod
    def find_outputs_variables(context):
        """
        Add Outputs Variables

        """

        vs_outputs = {}

        for setting in context.settings:
            prop = get_propertygroup(setting)
            conf = context.settings[setting]['conf']
            arch = context.settings[setting]['arch']
            if conf not in vs_outputs:
                vs_outputs[conf] = {}
            if arch not in vs_outputs[conf]:
                vs_outputs[conf][arch] = None

            if not vs_outputs[conf][arch]:
                vs_outputs[conf][arch] = context.vcxproj['tree'].find(
                    '%s/ns:OutDir' % prop, namespaces=context.vcxproj['ns']
                )
                if vs_outputs[conf][arch] is None:
                    vs_output = context.vcxproj['tree'].xpath(
                        '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir',
                        namespaces=context.vcxproj['ns'])
                    if vs_output:
                        vs_outputs[conf][arch] = vs_output[0]
                if vs_outputs[conf][arch] is None:
                    vs_output = context.vcxproj['tree'].xpath(
                        '//ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"]'
                        .format(setting), namespaces=context.vcxproj['ns'])
                    if vs_output:
                        vs_outputs[conf][arch] = vs_output[0]

            output_name = '$(ProjectName)'  # default
            output_name_node = context.vcxproj['tree'].find(
                '{0}/ns:TargetName'.format(prop), namespaces=context.vcxproj['ns']
            )
            if output_name_node is not None:
                output_name = output_name_node.text
            context.settings[setting]['output_name'] = cleaning_output(output_name)

        for setting in context.settings:
            conf = context.settings[setting]['conf']
            arch = context.settings[setting]['arch']

            output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

            if not context.cmake_output:
                    if vs_outputs[conf][arch] is not None:
                        output_path = cleaning_output(vs_outputs[conf][arch].text)
                    else:
                        output_path = cleaning_output(output_path)
            else:
                if context.cmake_output[-1:] == '/' or context.cmake_output[-1:] == '\\':
                    build_type = '${CMAKE_BUILD_TYPE}'
                else:
                    build_type = '/${CMAKE_BUILD_TYPE}'
                output_path = context.cmake_output + build_type

            output_path = output_path.strip().replace('\n', '')
            context.settings[setting]['out_dir'] = output_path

            if output_path:
                message('Output {0} = {1}'.format(setting, output_path), '')
            else:  # pragma: no cover
                message('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')


class VFProjectVariables(ProjectVariables):
    """
         Class who defines all the CMake variables to be used by the Fortran project
    """

    @staticmethod
    def find_outputs_variables(context):
        """
             Add Outputs Variables
        """

        for setting in context.settings:
            arch = context.settings[setting]['arch']

            output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

            if not context.cmake_output:
                if 'out_dir' in context.settings[setting]:
                    output_path = cleaning_output(context.settings[setting]['out_dir'])
                else:
                    output_path = cleaning_output(output_path)
            else:
                if context.cmake_output[-1:] == '/' or context.cmake_output[-1:] == '\\':
                    build_type = '${CMAKE_BUILD_TYPE}'
                else:
                    build_type = '/${CMAKE_BUILD_TYPE}'
                output_path = context.cmake_output + build_type

            output_path = output_path.strip().replace('\n', '')
            context.settings[setting]['out_dir'] = output_path

            if output_path:
                message('Output {0} = {1}'.format(setting, output_path), '')
            else:  # pragma: no cover
                message('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')
