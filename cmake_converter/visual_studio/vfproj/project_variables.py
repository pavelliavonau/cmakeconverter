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

from cmake_converter.project_variables import ProjectVariables


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

    def set_import_library(self, context, flag_name, import_library, node):
        del flag_name, node

        self.set_path_and_name_from_node(
            context,
            'Import library',
            import_library,
            'ARCHIVE_OUTPUT_DIRECTORY',
            'ARCHIVE_OUTPUT_NAME'
        )

    def set_program_database_file(self, context, flag_name, program_database_file, node):
        del flag_name, node
        self.set_path_and_name_from_node(
            context,
            'Program database',
            program_database_file,
            'PDB_OUTPUT_DIRECTORY',
            'PDB_NAME'
        )