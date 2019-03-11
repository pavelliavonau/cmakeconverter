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
    check_for_relative_in_path, set_native_slash, write_property_of_settings, write_comment, \
    is_settings_has_data


class VCXProjectVariables(ProjectVariables):
    """
        Class who defines all the CMake variables to be used by the C/C++ project
    """

    @staticmethod
    def set_root_namespace(context, node):
        context.root_namespace = node.text

    def set_output_dir(self, context, node):
        self.set_output_dir_impl(context, node.text)

    def set_output_file(self, context, output_file_node):
        if output_file_node is not None:
            self.set_output_file_impl(context, output_file_node.text)

    @staticmethod
    def set_import_library(context, node):
        import_library_file = node.text
        import_library_file = set_native_slash(import_library_file)
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

        context.settings[context.current_setting]['ARCHIVE_OUTPUT_DIRECTORY'] = [import_library_path]
        context.settings[context.current_setting]['ARCHIVE_OUTPUT_NAME'] = [import_library_name]
