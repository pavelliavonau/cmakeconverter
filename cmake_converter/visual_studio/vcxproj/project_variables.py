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
from cmake_converter.data_files import get_propertygroup


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

            target_name = '$(ProjectName)'  # default
            target_name_node = context.vcxproj['tree'].find(
                '{0}/ns:TargetName'.format(prop), namespaces=context.vcxproj['ns']
            )
            if target_name_node is None:
                target_name_node = context.vcxproj['tree'].find(
                    '//ns:TargetName[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"]'
                    .format(setting),
                    namespaces=context.vcxproj['ns']
                )

            if target_name_node is not None:
                target_name = target_name_node.text
            context.settings[setting]['target_name'] = cleaning_output(target_name)

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
