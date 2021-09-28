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
    Module for project files properties for Fortran projects
"""

import re
import os

from cmake_converter.project_files import ProjectFiles
from cmake_converter.utils import message


class VFProjectFiles(ProjectFiles):
    """
        Class project files properties for Fortran projects
    """

    def include_directive_case_check(self, context, file_path_name, file_lists_for_include_paths):
        """
        Check for absence of files at include directives (case sensitive)

        :param context:
        :param file_path_name:
        :param file_lists_for_include_paths:
        :return:
        """
        includes_re = re.compile(
            r'include \'(.*)\'', re.IGNORECASE
        )
        file_abs_path = os.path.join(os.path.dirname(context.vcxproj_path), file_path_name)

        file_text = ''
        with open(file_abs_path, 'r', errors='replace', encoding='utf-8') as file:
            file_text = file.read()
        includes = includes_re.findall(file_text)

        checked_includes = set()
        for include_name_in_file in includes:
            if include_name_in_file in checked_includes:
                continue
            checked_includes.add(include_name_in_file)

            include_file_path, include_file_name = os.path.split(include_name_in_file)

            # add current file path to search list helper
            current_file_path = os.path.normpath(os.path.dirname(file_abs_path))
            if os.path.exists(current_file_path):
                file_lists_for_include_paths[current_file_path] = set(os.listdir(current_file_path))

            if not self.search_file_in_paths(
                    file_lists_for_include_paths,
                    include_file_path,
                    include_file_name):
                message(context, 'include {} from file {} not found'
                        .format(include_name_in_file, file_path_name), 'error')

    @staticmethod
    def search_file_in_paths(file_lists_for_include_paths, include_file_path, include_file_name):
        """
        Search of file at filesystem(cached) case sensitive

        :param file_lists_for_include_paths:
        :param include_file_path:
        :param include_file_name:
        :return:
        """
        found = False
        file_lists_for_includes_with_paths = {}
        for include_path in file_lists_for_include_paths:
            joined_include_path = os.path.normpath(os.path.join(include_path, include_file_path))
            files = {}
            if joined_include_path in file_lists_for_include_paths:
                files = file_lists_for_include_paths[joined_include_path]
            else:
                if os.path.exists(joined_include_path):
                    files = set(os.listdir(joined_include_path))
                    file_lists_for_includes_with_paths[joined_include_path] = files

            if include_file_name in files:
                found = True
                break

        file_lists_for_include_paths.update(file_lists_for_includes_with_paths)

        return found
