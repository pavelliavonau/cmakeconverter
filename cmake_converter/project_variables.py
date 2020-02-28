#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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

from cmake_converter.utils import replace_vs_vars_with_cmake_vars
from cmake_converter.utils import cleaning_output, message, check_for_relative_in_path
from cmake_converter.utils import set_native_slash, get_dir_name_with_vars


class ProjectVariables:
    """
        Class that manages project variables
    """

    @staticmethod
    def set_target_name(context, target_name_value):
        """ Evaluates target name and sets it into project context """
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
        output_path = output_path.replace('\n', '')
        output_path = check_for_relative_in_path(context, output_path)
        context.settings[context.current_setting]['OUTPUT_DIRECTORY'] = [output_path]
        message(context, 'Output Dir = {}'.format(output_path), '')

    @staticmethod
    def set_output_file_impl(context, output_file_node_text):
        """ Common routine for evaluating path and name of output file """
        if output_file_node_text:
            # next 2 properties are special. check Default.cmake for understanding
            if not context.settings[context.current_setting]['OUTPUT_DIRECTORY']:
                context.settings[context.current_setting]['OUTPUT_DIRECTORY'] = \
                    ['${OUTPUT_DIRECTORY}']
            if not context.settings[context.current_setting]['TARGET_NAME']:
                context.settings[context.current_setting]['TARGET_NAME'] = ['${TARGET_NAME}']

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
    def set_path_and_name_from_node(context, node_name, file_path, path_property, name_property):
        """ Common routine for evaluating path and name from node text """
        if not file_path:
            return

        file_path = replace_vs_vars_with_cmake_vars(context, file_path)
        file_path = set_native_slash(file_path)
        path, name = get_dir_name_with_vars(context, file_path)
        result_name = replace_vs_vars_with_cmake_vars(context, name)
        result_path = cleaning_output(context, path)
        result_path = check_for_relative_in_path(context, result_path)

        message(context, '{} directory = {}'.format(node_name, result_path), '')
        message(context, '{} name = {}'.format(node_name, result_name), '')

        context.settings[context.current_setting][path_property] = [result_path]
        context.settings[context.current_setting][name_property] = [result_name]
