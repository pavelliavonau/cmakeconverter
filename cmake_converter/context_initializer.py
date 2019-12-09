#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019:
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
Module that is responsible for common context initialization.
"""

import os

from cmake_converter.utils import message


class ContextInitializer:
    """
    Module that holds common stuff for context initialization.
    """
    def __init__(self, context, vs_project, cmake_lists_destination_path):
        self.init_files(context, vs_project, cmake_lists_destination_path)
        message(
            context,
            'Initialization data for conversion of project {0}'.format(context.vcxproj_path),
            ''
        )
        for sln_config in context.sln_configurations_map:
            context.configurations_to_parse.add(context.sln_configurations_map[sln_config])

    def init_context(self, context, vs_project):
        """
        Initialize context

        """

    def init_files(self, context, vs_project, cmake_lists):
        """
        Initialize opening of CMakeLists.txt and VS Project files

        :param context: converter context
        :type context: Context
        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake_lists: CMakeLists.txt file path
        :type cmake_lists: str
        """

        if vs_project:
            temp_path = os.path.splitext(vs_project)
            project_name = os.path.basename(temp_path[0])
            context.project_name = project_name
            context.vcxproj_path = vs_project
            self.init_context(context, vs_project)
            self.set_cmake_lists_path(context, cmake_lists)

    @staticmethod
    def set_cmake_lists_path(context, cmake_lists):
        """
        Set CMakeLists.txt path in context, for given project

        :param context: converter context
        :type context: Context
        :param cmake_lists: path of CMakeLists related to project name
        :type cmake_lists: str
        """

        context_cmake = None

        if cmake_lists:
            if os.path.exists(cmake_lists):
                context_cmake = cmake_lists

        if context_cmake is None:
            message(
                context,
                'Path "{}" for CMakeLists.txt is wrong. '
                'It will be created in working directory.'.format(cmake_lists),
                'warn'
            )
            context_cmake = 'CMakeLists.txt'

        if context:
            context.cmake = context_cmake

        return context_cmake
