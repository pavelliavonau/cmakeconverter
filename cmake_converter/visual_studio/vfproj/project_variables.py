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
from cmake_converter.utils import cleaning_output, message

import os


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

            output_file = ''
            if 'VFLinkerTool' in context.settings[setting]:
                output_file = context.settings[setting]['VFLinkerTool'].get('OutputFile')
            if 'VFLibrarianTool' in context.settings[setting]:
                output_file = context.settings[setting]['VFLibrarianTool'].get('OutputFile')

            if output_file:
                path = os.path.dirname(output_file)
                name, ext = os.path.splitext(os.path.basename(output_file))
                output_path = cleaning_output(path)
                context.settings[setting]['target_name'] = cleaning_output(name)

            context.settings[setting]['out_dir'] = output_path

            if output_path:
                message('Output {0} = {1}'.format(setting, output_path), '')
            else:  # pragma: no cover
                message('No Output found. Use [{0}/bin] by default !'.format(arch), 'warn')
