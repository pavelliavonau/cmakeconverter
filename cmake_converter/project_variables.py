#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Matthieu Estrada, ttamalfor@gmail.com
#   Pavel Liavonau, liavonlida@gmail.com
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

import os

from cmake_converter.utils import write_property_of_settings
from cmake_converter.utils import write_comment, replace_vs_vars_with_cmake_vars
from cmake_converter.utils import cleaning_output, message, check_for_relative_in_path


class ProjectVariables:
    """
        Class who manage project variables
    """

    @staticmethod
    def apply_default_values(context):
        output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value
        output_path = cleaning_output(context, output_path)
        context.settings[context.current_setting]['out_dir'] = [output_path]

        target_name = '$(ProjectName)'  # default value
        context.settings[context.current_setting]['target_name'] = [replace_vs_vars_with_cmake_vars(
            context,
            target_name
        )]

    @staticmethod
    def set_target_name(context, target_name_value):
        context.settings[context.current_setting]['target_name'] = [replace_vs_vars_with_cmake_vars(
            context,
            target_name_value
        )]
        message(context, 'TargetName = {}'.format(target_name_value), '')

    @staticmethod
    def set_output_dir_impl(context, output_node_text):
        output_path = ''
        if not context.cmake_output:
            output_path = cleaning_output(context, output_node_text)
        else:
            if context.cmake_output[-1:] == '/' or context.cmake_output[-1:] == '\\':
                build_type = '${CMAKE_BUILD_TYPE}'
            else:
                build_type = '/${CMAKE_BUILD_TYPE}'
            output_path = context.cmake_output + build_type

        output_path = output_path.strip().replace('\n', '')
        output_path = check_for_relative_in_path(context, output_path)
        context.settings[context.current_setting]['out_dir'] = [output_path]
        message(context, 'Output Dir = {0}'.format(output_path), '')

    @staticmethod
    def set_output_file_impl(context, output_file_node_text):
        if output_file_node_text:
            output_path = context.settings[context.current_setting]['out_dir'][0]
            output_file = cleaning_output(context, output_file_node_text)
            output_file = output_file.replace('${OUT_DIR}', output_path)
            output_path = os.path.dirname(output_file)
            name, _ = os.path.splitext(os.path.basename(output_file))
            name = name.replace(
                '${TARGET_NAME}',
                context.settings[context.current_setting]['target_name'][0]
            )
            context.settings[context.current_setting]['target_name'] = \
                [replace_vs_vars_with_cmake_vars(context, name)]

            output_path = check_for_relative_in_path(context, output_path)
            context.settings[context.current_setting]['out_dir'] = [output_path]

        message(
            context,
            'Output File : dir="{}" name="{}"'.format(
                context.settings[context.current_setting]['out_dir'][0],
                context.settings[context.current_setting]['target_name']),
            '')

    @staticmethod
    def write_target_outputs(context, cmake_file):
        """
        Add outputs for each artefacts CMake target

        :param context: related full context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if not context.settings:
            return

        write_comment(cmake_file, 'Target name')
        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            begin_text='string(CONCAT TARGET_NAME',
            end_text=')',
            property_name='target_name',
            default='${PROJECT_NAME}'
        )
        cmake_file.write(
            'set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME ${TARGET_NAME})\n\n'
        )

        write_comment(cmake_file, 'Output directory')

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            begin_text='string(CONCAT OUT_DIR',
            end_text=')',
            property_name='out_dir',
            default='${CMAKE_SOURCE_DIR}/${CMAKE_VS_PLATFORM_NAME}/$<CONFIG>'
        )

        any_setting = None
        for setting in context.settings:
            any_setting = setting
            if any_setting is not None:
                break

        configuration_type = context.settings[any_setting]['target_type']

        if configuration_type == 'DynamicLibrary':
            cmake_file.write('set(ARCHIVE_OUT_DIR ${OUT_DIR})\n')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                begin_text='string(CONCAT ARCHIVE_OUT_DIR',
                end_text=')',
                property_name='import_library_path',
            )
            cmake_file.write('set(ARCHIVE_OUT_NAME ${PROJECT_NAME})\n')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                begin_text='string(CONCAT ARCHIVE_OUT_NAME',
                end_text=')',
                property_name='import_library_name',
            )

        if configuration_type:
            left_string = 'set_target_properties(${PROJECT_NAME} PROPERTIES '
            right_string = '_OUTPUT_DIRECTORY ${OUT_DIR})\n'
            if configuration_type in ('DynamicLibrary', 'StaticLibrary'):
                if configuration_type == 'DynamicLibrary':
                    cmake_file.write(
                        left_string + 'ARCHIVE' + '_OUTPUT_NAME ${ARCHIVE_OUT_NAME})\n')
                    cmake_file.write(
                        left_string + 'ARCHIVE' + '_OUTPUT_DIRECTORY ${ARCHIVE_OUT_DIR})\n')
                    cmake_file.write(left_string + 'RUNTIME' + right_string)
                else:
                    cmake_file.write(
                        left_string + 'ARCHIVE' + right_string)
                # TODO: do we really need LIBRARY_OUTPUT_DIRECTORY here?
                cmake_file.write(left_string + 'LIBRARY' + right_string)
                cmake_file.write('\n')
            else:
                cmake_file.write(
                    left_string + 'RUNTIME' + right_string + '\n')
