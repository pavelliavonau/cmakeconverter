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

import re
import os

from cmake_converter.project_files import ProjectFiles
from cmake_converter.utils import message


class VFProjectFiles(ProjectFiles):

    def include_directive_case_check(self, context, file_path_name, file_lists_for_include_paths):
        includes_re = re.compile(
            r'include \'(.*)\'', re.IGNORECASE
        )
        working_path = os.path.dirname(context.vcxproj_path)
        file_abs_path = os.path.join(working_path, file_path_name)
        file = open(file_abs_path, 'r', errors='replace')
        file_text = file.read()
        file.close()
        includes = includes_re.findall(file_text)

        checked_includes = set()
        for include_name_in_file in includes:
            if include_name_in_file in checked_includes:
                continue
            checked_includes.add(include_name_in_file)
            include_file_path, include_file_name = os.path.split(include_name_in_file)

            abs_source_path = os.path.dirname(file_abs_path)
            if os.path.exists(abs_source_path):
                file_lists_for_include_paths[abs_source_path] \
                    = os.listdir(abs_source_path)

            found = False
            for include_path in file_lists_for_include_paths:
                files = file_lists_for_include_paths[include_path]
                if include_name_in_file in files:
                    found = True
                    break

            # try to search in relative path
            if not found:
                file_lists_for_relative_include_paths = {}
                for setting in context.settings:
                    for include_path in context.settings[setting]['inc_dirs_list']:
                        if include_path not in file_lists_for_relative_include_paths:
                            abs_include_path = os.path.join(working_path, include_path)
                            abs_include_path_relative = os.path.join(abs_include_path,
                                                                     include_file_path)
                            if os.path.exists(abs_include_path_relative):
                                file_lists_for_relative_include_paths[include_path] = os.listdir(
                                    abs_include_path_relative)
                for include_path in file_lists_for_relative_include_paths:
                    files = file_lists_for_relative_include_paths[include_path]
                    if include_file_name in files:
                        found = True
                        break
            if not found:
                message(context, 'include {0} in file {1} not found'
                        .format(include_name_in_file, file_path_name), 'error')
            file_lists_for_include_paths.pop(abs_source_path)
