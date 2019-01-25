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

import os

from cmake_converter.project_variables import ProjectVariables
from cmake_converter.utils import cleaning_output, message, replace_vs_vars_with_cmake_vars, \
    check_for_relative_in_path


class VCXProjectVariables(ProjectVariables):
    """
        Class who defines all the CMake variables to be used by the C/C++ project
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
    def set_output_dir(context, node):
        output_path = ''
        if not context.cmake_output:
            output_path = cleaning_output(context, node.text)
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
    def set_output_file(context, output_file_node):
        output_path = context.settings[context.current_setting]['out_dir'][0]
        if output_file_node is not None:
            output_file = output_file_node.text
            output_file = cleaning_output(context, output_file)
            output_file = output_file.replace('${OUT_DIR}', output_path)
            output_path = os.path.dirname(output_file)
            name, _ = os.path.splitext(os.path.basename(output_file))
            name = name.replace(
                '${TARGET_NAME}',
                context.settings[context.current_setting]['target_name'][0]
            )
            context.settings[context.current_setting]['target_name'] =\
                [replace_vs_vars_with_cmake_vars(context, name)]

        output_path = check_for_relative_in_path(context, output_path)
        context.settings[context.current_setting]['out_dir'] = [output_path]

        message(
            context,
            'Output File : dir="{}" name="{}"'.format(
                output_path, context.settings[context.current_setting]['target_name']),
            '')

    @staticmethod
    def set_import_library(context, node):
        import_library_file = node.text
        path = os.path.dirname(import_library_file)
        name, _ = os.path.splitext(os.path.basename(import_library_file))
        import_library_path = cleaning_output(context, path)
        import_library_name = replace_vs_vars_with_cmake_vars(context, name)
        import_library_path = check_for_relative_in_path(context, import_library_path)
        message(
            context,
            '{0} : Import library path = {1}'.format(context.current_setting, import_library_path),
            '')
        message(
            context,
            '{0} : Import library name = {1}'.format(context.current_setting, import_library_name),
            '')

        context.settings[context.current_setting]['import_library_path'] = [import_library_path]
        context.settings[context.current_setting]['import_library_name'] = [import_library_name]
