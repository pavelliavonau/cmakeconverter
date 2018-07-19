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
from cmake_converter.utils import cleaning_output, message, replace_vs_vars_with_cmake_vars,\
    check_for_relative_in_path

import os


class VFProjectVariables(ProjectVariables):
    """
         Class who defines all the CMake variables to be used by the Fortran project
    """

    @staticmethod
    def find_outputs_variables(context, setting):
        """
             Add Outputs Variables
        """

        arch = context.settings[setting]['arch']

        output_path = '$(SolutionDir)$(Platform)/$(Configuration)/'  # default value

        if not context.cmake_output:
            if 'out_dir' in context.settings[setting]:
                output_path = context.settings[setting]['out_dir']
            output_path = cleaning_output(context, output_path)
        else:
            if context.cmake_output[-1:] == '/' or context.cmake_output[-1:] == '\\':
                build_type = '${CMAKE_BUILD_TYPE}'
            else:
                build_type = '/${CMAKE_BUILD_TYPE}'
            output_path = context.cmake_output + build_type

        output_path = output_path.strip().replace('\n', '')

        output_file = ''
        if 'VFLinkerTool' in context.settings[setting]:
            output_file = context.settings[setting]['VFLinkerTool'].get('OutputFile')
        if 'VFLibrarianTool' in context.settings[setting]:
            output_file = context.settings[setting]['VFLibrarianTool'].get('OutputFile')

        if output_file:
            path = os.path.dirname(output_file)
            name, ext = os.path.splitext(os.path.basename(output_file))
            path = cleaning_output(context, path)
            output_path = path.replace('${OUT_DIR}', output_path)
            context.settings[setting]['target_name'] = replace_vs_vars_with_cmake_vars(
                context,
                name
            )

        output_path = check_for_relative_in_path(context, output_path)
        context.settings[setting]['out_dir'] = output_path

        if output_path:
            message(context, 'Output {0} = {1}'.format(setting, output_path), '')
        else:  # pragma: no cover
            message(context, 'No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')

        import_library = ''
        if 'VFLinkerTool' in context.settings[setting]:
            import_library = context.settings[setting]['VFLinkerTool'].get('ImportLibrary')
        if 'VFLibrarianTool' in context.settings[setting]:
            import_library = context.settings[setting]['VFLibrarianTool'].get('ImportLibrary')

        import_library_path = ''
        import_library_name = ''
        if import_library:
            import_library_file = import_library
            path = os.path.dirname(import_library_file)
            name, ext = os.path.splitext(os.path.basename(import_library_file))
            import_library_path = cleaning_output(context, path)
            import_library_name = replace_vs_vars_with_cmake_vars(context, name)
            import_library_path = check_for_relative_in_path(context, import_library_path)
            message(context, '{0} : Import library path = {1}'.format(setting, import_library_path),
                    '')
            message(context, '{0} : Import library name = {1}'.format(setting, import_library_name),
                    '')

        context.settings[setting]['import_library_path'] = import_library_path
        context.settings[setting]['import_library_name'] = import_library_name

