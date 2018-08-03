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

"""
    ProjectFiles
    =============
     Manages the recovery of project files
"""

import os

from cmake_converter.utils import take_name_from_list_case_ignore, normalize_path
from cmake_converter.utils import message, write_comment


class ProjectFiles(object):
    """
        Class who collect and store project files
    """

    def __init__(self):
        self.languages = []
        self.file_lists = {}
        self.file_lists_for_include_paths = {}

    def parse_file_node_options(self, context, file_node, node_text):
        pass

    def include_directive_case_check(self, context, file_name, file_lists_for_include_paths):
        pass

    def add_file_from_node(self, context, files_dest_dict, file_node,
                           file_node_attr, source_group):
        if file_node.get(file_node_attr) is not None:
            node_text = str(file_node.get(file_node_attr))
            node_text = '/'.join(node_text.split('\\'))
            if not node_text.rpartition('.')[-1] in self.languages:
                self.languages.append(node_text.rpartition('.')[-1])
            file_path, file_name = os.path.split(node_text)
            if file_path not in self.file_lists:
                vcxproj_dir = os.path.dirname(context.vcxproj_path)
                self.file_lists[file_path] = []
                if os.path.exists(os.path.join(vcxproj_dir, file_path)):
                    self.file_lists[file_path] = os.listdir(os.path.join(vcxproj_dir, file_path))
            if file_path not in files_dest_dict:
                files_dest_dict[file_path] = []
            if file_name not in files_dest_dict[file_path]:
                real_name = take_name_from_list_case_ignore(context, self.file_lists[file_path],
                                                            file_name)
                if real_name:
                    name_to_add = real_name
                else:
                    name_to_add = file_name
                    message(context, 'Adding absent {} file into project files'
                            .format(file_name), 'warn')

                files_dest_dict[file_path].append(name_to_add)
                if file_path:
                    file_path = file_path + '/'
                file_path_name = file_path + name_to_add
                if source_group not in context.source_groups:
                    context.source_groups[source_group] = []
                context.source_groups[source_group].append(file_path_name)
                context.source_groups[source_group].sort(key=str.lower)
                self.parse_file_node_options(context, file_node, file_path_name)
                if real_name:
                    self.include_directive_case_check(context,
                                                      file_path_name,
                                                      self.file_lists_for_include_paths)

    def init_file_lists_for_include_paths(self, context):
        """
        For include directive case ad path checking. Works only with vfproj.
        :param context:
        :return:
        """
        vcxproj_dir = os.path.dirname(context.vcxproj_path)
        for setting in context.settings:
            for include_path in context.settings[setting]['inc_dirs_list']:
                if include_path not in self.file_lists_for_include_paths:
                    abs_include_path = os.path.join(vcxproj_dir, include_path)
                    if os.path.exists(abs_include_path):
                        self.file_lists_for_include_paths[include_path]\
                            = os.listdir(abs_include_path)

    def apply_files_to_context(self, context):
        has_headers = True if context.headers else False
        context.has_headers = has_headers
        context.has_only_headers = True if has_headers and not context.sources else False
        message(context, "Source files extensions found: {0}".format(self.languages), 'INFO')

    def find_cmake_project_languages(self, context):
        """
        Add CMake Project

        """

        cpp_extensions = ['cc', 'cp', 'cxx', 'cpp', 'CPP', 'c++', 'C']

        available_language = {'c': 'C'}
        available_language.update(dict.fromkeys(cpp_extensions, 'CXX'))

        fortran_extensions = ['F90', 'F', 'f90', 'f', 'fi', 'FI']
        available_language.update(dict.fromkeys(fortran_extensions, 'Fortran'))

        project_languages_set = set()
        for l in self.languages:
            if l in available_language:
                project_languages_set.add(available_language[l])

        project_languages = list(project_languages_set)
        project_languages.sort()
        for project_language in project_languages:
            context.solution_languages.add(project_language)
        context.project_languages = project_languages

    @staticmethod
    def write_cmake_project(context, cmake_file):
        """
        Write cmake project for given CMake file

        :param context: Converter context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        lang = ''
        if context.project_languages:
            lang = ' ' + ' '.join(context.project_languages)
        if context.project_name == '':
            message(
                context,
                'No PROJECT NAME found or define. '
                'Check it!!',
                'error'
            )
        cmake_file.write('project({0}{1})\n\n'.format(context.project_name, lang))

    @staticmethod
    def get_source_group_var(source_group_name):
        if not source_group_name:
            return 'no_group_source_files'
        else:
            source_group_name = source_group_name.replace(' ', '_')
            return source_group_name.replace('\\\\', '__')

    def write_source_groups(self, context, cmake_file):
        write_comment(cmake_file, 'Source groups')
        working_path = os.path.dirname(context.vcxproj_path)

        for source_group in sorted(context.source_groups):
            source_group_var = self.get_source_group_var(source_group)
            cmake_file.write('set({}\n'.format(source_group_var))
            for src_file in context.source_groups[source_group]:
                cmake_file.write('    {0}\n'
                                 .format(normalize_path(context, working_path,
                                                        src_file,
                                                        False)))

            cmake_file.write(')\n')
            cmake_file.write(
                'source_group("{}" FILES ${{{}}})\n\n'.format(source_group, source_group_var)
            )

        cmake_file.write('set(ALL_FILES ')
        for source_group in context.source_groups:
            cmake_file.write(
                ' ${{{}}}'.format(context.files.get_source_group_var(source_group))
            )
        cmake_file.write(')\n\n')

    @staticmethod
    def add_additional_code(context, file_to_add, cmake_file):
        """
        Add additional file with CMake code inside

        :param context: the context of converter
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        :param file_to_add: the file who contains CMake code
        :type file_to_add: str
        """

        if file_to_add != '':
            try:
                fc = open(file_to_add)
                write_comment(cmake_file, 'Provides from external file.')
                for line in fc:
                    cmake_file.write(line)
                fc.close()
                cmake_file.write('\n')
                message(context, 'File of Code is added = ' + file_to_add, 'warn')
            except OSError as e:
                message(context, str(e), 'error')
                message(
                    context,
                    'Wrong data file ! Code was not added, please verify file name or path !',
                    'error'
                )
