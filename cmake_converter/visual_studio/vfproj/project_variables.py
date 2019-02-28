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
from cmake_converter.utils import cleaning_output, message, replace_vs_vars_with_cmake_vars,\
    check_for_relative_in_path, set_native_slash


class VFProjectVariables(ProjectVariables):
    """
         Class who defines all the CMake variables to be used by the Fortran project
    """

    def set_output_dir(self, context, attr_name, output_dir, node):
        del attr_name, node

        self.set_output_dir_impl(context, output_dir)

    def set_output_file(self, context, flag_name, output_file, node):
        del flag_name, node

        self.set_output_file_impl(context, output_file)

    @staticmethod
    def set_import_library(context, flag_name, import_library, node):
        del flag_name, node

        import_library_path = ''
        import_library_name = ''
        if import_library:
            import_library_file = import_library
            import_library_file = set_native_slash(import_library_file)
            path = os.path.dirname(import_library_file)
            name, _ = os.path.splitext(os.path.basename(import_library_file))
            import_library_path = cleaning_output(context, path)
            import_library_name = replace_vs_vars_with_cmake_vars(context, name)
            import_library_path = check_for_relative_in_path(context, import_library_path)
            message(context, 'Import library path = {0}'.format(import_library_path), '')
            message(context, 'Import library name = {0}'.format(import_library_name), '')

        context.settings[context.current_setting]['import_library_path'] = [import_library_path]
        context.settings[context.current_setting]['import_library_name'] = [import_library_name]
