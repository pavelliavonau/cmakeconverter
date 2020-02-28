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
    Dependencies
    ============
     Manage directories and libraries of project dependencies
"""

import ntpath
import os
import re

from cmake_converter.data_files import get_vcxproj_data
from cmake_converter.utils import get_global_project_name_from_vcxproj_file, normalize_path, message
from cmake_converter.utils import replace_vs_vars_with_cmake_vars, resolve_path_variables_of_vs


class Dependencies:
    """
        Class who find and write dependencies of project, additional directories...
    """

    @staticmethod
    def set_additional_include_directories(aid_text, setting, context):
        """
        Return additional include directories of given context

        :param aid_text: path to sources
        :type aid_text: str
        :param setting: current setting (Debug|x64, Release|Win32,...)
        :type setting: str
        :param context: current context
        :type context: Context
        :return: include directories of context, separated by semicolons
        :rtype: str
        """

        if not aid_text:
            return

        working_path = os.path.dirname(context.vcxproj_path)
        inc_dir = resolve_path_variables_of_vs(context, aid_text)
        inc_dir = inc_dir.replace('%(AdditionalIncludeDirectories)', '')
        inc_dirs = context.settings[setting]['inc_dirs']
        dirs_raw = []
        for i in inc_dir.split(';'):
            if i:
                dirs_raw.append(i)
                i = normalize_path(context, working_path, i)
                i = replace_vs_vars_with_cmake_vars(context, i)
                inc_dirs.append(i)

        context.settings[setting]['inc_dirs_list'].extend(dirs_raw)

        if inc_dirs:
            message(
                context,
                'Include Directories : {}'.format(context.settings[setting]['inc_dirs']),
                '')

    @staticmethod
    def set_target_additional_dependencies_impl(context, dependencies_text, splitter):
        """ Implementation of Handler for additional link dependencies """
        dependencies_text = dependencies_text.replace('%(AdditionalDependencies)', '')
        add_libs = []
        for d in re.split(splitter, dependencies_text):
            if d:
                d = re.sub(r'\.lib$', '', d, 0, re.IGNORECASE)  # strip lib extension
                add_libs.append(d)

        if add_libs:
            context.add_lib_deps = True
            message(context, 'Additional Dependencies : {}'.format(add_libs), '')
            context.settings[context.current_setting]['add_lib_deps'] = add_libs

    @staticmethod
    def get_dependency_target_name(context, vs_project):
        """
        Return dependency target name

        :param context: the context of converter
        :type context: Context
        :param vs_project: path to ".vcxproj" file
        :type vs_project: str
        :return: target name
        :rtype: str
        """

        vcxproj = get_vcxproj_data(context, vs_project)
        project_name = get_global_project_name_from_vcxproj_file(vcxproj)

        if project_name:
            return project_name

        return os.path.splitext(ntpath.basename(vs_project))[0]
