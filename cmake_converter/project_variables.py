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

from cmake_converter.utils import write_property_of_settings, is_settings_has_data
from cmake_converter.utils import write_comment, replace_vs_vars_with_cmake_vars
from cmake_converter.utils import cleaning_output, message, check_for_relative_in_path


class ProjectVariables:
    """
        Class who manage project variables
    """

    @staticmethod
    def set_target_name(context, target_name_value):
        context.settings[context.current_setting]['TARGET_NAME'] = [replace_vs_vars_with_cmake_vars(
            context,
            target_name_value
        )]
        message(context, 'TargetName = {}'.format(target_name_value), '')

    @staticmethod
    def set_output_dir_impl(context, output_node_text):
        """

        :param context:
        :param output_node_text:
        :return:
        """
        output_path = cleaning_output(context, output_node_text)
        output_path = output_path.strip().replace('\n', '')
        output_path = check_for_relative_in_path(context, output_path)
        context.settings[context.current_setting]['OUTPUT_DIRECTORY'] = [output_path]
        message(context, 'Output Dir = {0}'.format(output_path), '')

    @staticmethod
    def set_output_file_impl(context, output_file_node_text):
        if output_file_node_text:
            # TODO: remove next hack
            if not context.settings[context.current_setting]['OUTPUT_DIRECTORY']:
                context.settings[context.current_setting]['OUTPUT_DIRECTORY'] = ['']
            if not context.settings[context.current_setting]['TARGET_NAME']:
                context.settings[context.current_setting]['TARGET_NAME'] = ['']

            output_path = context.settings[context.current_setting]['OUTPUT_DIRECTORY'][0]
            output_file = cleaning_output(context, output_file_node_text)
            output_file = output_file.replace('${OUTPUT_DIRECTORY}', output_path)
            output_path = os.path.dirname(output_file)
            name, _ = os.path.splitext(os.path.basename(output_file))
            name = name.replace(
                '${TARGET_NAME}',
                context.settings[context.current_setting]['TARGET_NAME'][0]
            )
            context.settings[context.current_setting]['TARGET_NAME'] = \
                [replace_vs_vars_with_cmake_vars(context, name)]

            output_path = check_for_relative_in_path(context, output_path)
            context.settings[context.current_setting]['OUTPUT_DIRECTORY'] = [output_path]

            message(
                context,
                'Output File : dir="{}" name="{}"'.format(
                    context.settings[context.current_setting]['OUTPUT_DIRECTORY'][0],
                    context.settings[context.current_setting]['TARGET_NAME']),
                '')

    @staticmethod
    def write_target_property(cmake_file,
                              property_indent,
                              config_condition_expr,
                              property_value,
                              width,
                              **kwargs):
        width_diff = 0
        property_name = kwargs['property_name']

        config = ''
        if config_condition_expr is not None:
            config = '_' + config_condition_expr.replace('$<CONFIG:', '').replace('>', '') + ' '
            width_diff = len('$<CONFIG:>') - len('_ ')

        if property_value:
            for property_sheet_cmake in property_value:
                result_width = width - width_diff
                if result_width < 0:
                    result_width = 0
                cmake_file.write(
                    '{}    {}{:<{width}}"{}"\n'.format(
                        property_indent,
                        property_name,
                        config.upper(),
                        property_sheet_cmake,
                        width=result_width)
                )

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

        if context.root_namespace:
            cmake_file.write('set(ROOT_NAMESPACE {})\n\n'.format(context.root_namespace))

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'TARGET_NAME'):
            write_comment(cmake_file, 'Target name')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
                end_text=')',
                property_name='TARGET_NAME',
                write_setting_property_func=ProjectVariables.write_target_property
            )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'OUTPUT_DIRECTORY'):
            write_comment(cmake_file, 'Output directory')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
                end_text=')',
                property_name='OUTPUT_DIRECTORY',
                write_setting_property_func=ProjectVariables.write_target_property
            )

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='ARCHIVE_OUTPUT_DIRECTORY',
            write_setting_property_func=ProjectVariables.write_target_property
        )

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='ARCHIVE_OUTPUT_NAME',
            write_setting_property_func=ProjectVariables.write_target_property
        )

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='PDB_OUTPUT_DIRECTORY',
            write_setting_property_func=ProjectVariables.write_target_property
        )

