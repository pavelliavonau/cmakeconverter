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

from cmake_converter.dependencies import Dependencies
from cmake_converter.utils import message


class VFDependencies(Dependencies):

    @staticmethod
    def find_include_dir(context):
        for setting in context.settings:
            ad_inc = context.settings[setting]['VFFortranCompilerTool'].get(
                'AdditionalIncludeDirectories'
            )
            if ad_inc:
                Dependencies.get_additional_include_directories(ad_inc, setting, context)
            if 'inc_dirs' in context.settings[setting]:
                context.settings[setting]['inc_dirs'] += ';${CMAKE_CURRENT_SOURCE_DIR}/'
            else:
                context.settings[setting]['inc_dirs'] = '${CMAKE_CURRENT_SOURCE_DIR}/'

    @staticmethod
    def find_target_additional_dependencies(context):
        for setting in context.settings:
            context.add_lib_deps = []
            ad_libs = None
            if 'VFLibrarianTool' in context.settings[setting]:
                ad_libs = context.settings[setting]['VFLibrarianTool'].get('AdditionalDependencies')
            if 'VFLinkerTool' in context.settings[setting]:
                ad_libs = context.settings[setting]['VFLinkerTool'].get('AdditionalDependencies')
            if ad_libs:
                message('Additional Dependencies = {0}'.format(ad_libs), '')
                add_lib_dirs = []
                for d in ad_libs.split(';'):
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            add_lib_dirs.append(d.replace('.lib', ''))
                context.add_lib_deps = add_lib_dirs
            else:
                message('No additional dependencies.', '')
            break

    @staticmethod
    def find_target_additional_library_directories(context):
        """
        Find and set additional library directories in context

        """

        for setting in context.settings:
            context.add_lib_dirs = []
            additional_library_directories = None
            if 'VFLibrarianTool' in context.settings[setting]:
                additional_library_directories = context.settings[setting]['VFLibrarianTool'] \
                    .get('AdditionalLibraryDirectories')
            if 'VFLinkerTool' in context.settings[setting]:
                additional_library_directories = context.settings[setting]['VFLinkerTool'] \
                    .get('AdditionalLibraryDirectories')

            if additional_library_directories:
                list_depends = additional_library_directories.replace(
                    '%(AdditionalLibraryDirectories)', ''
                )
                if list_depends != '':
                    message('Additional Library Directories = {0}'.format(list_depends), '')
                    add_lib_dirs = []
                    for d in list_depends.split(';'):
                        d = d.strip()
                        if d != '':
                            add_lib_dirs.append(d)
                    context.add_lib_dirs = add_lib_dirs
            else:  # pragma: no cover
                message('No additional library dependencies.', '')