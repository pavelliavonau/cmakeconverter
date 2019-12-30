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
    ProjectFiles
    =============
     Manages the recovery of project files
"""

import os
import copy

from cmake_converter.utils import take_name_from_list_case_ignore, normalize_path
from cmake_converter.utils import message, write_comment, make_cmake_literal


class ProjectFiles:
    """
        Class that collects and store project files
    """

    def __init__(self):
        self.languages = []
        self.file_lists = {}
        self.file_lists_for_include_paths = {}

    def include_directive_case_check(self, context, file_path_name, file_lists_for_include_paths):
        """ Dummy to fix crash """

    @staticmethod
    def __create_file_context(context):
        file_context = copy.copy(context)
        file_context.settings = {}
        file_context.flags = copy.copy(context.flags)
        file_context.flags.__init__()
        file_context.sln_configurations_map = copy.copy(context.sln_configurations_map)
        file_context.file_contexts = None
        file_context.warnings_count = 0
        for setting in context.settings:       # copy settings
            file_context.current_setting = setting
            file_context.utils.init_context_current_setting(file_context)
        context.current_setting = (None, None)
        return file_context

    def __add_file_into_container(self, context, **kwargs):

        files_container = kwargs['files_container']
        file_path = kwargs['file_path']
        file_name = kwargs['file_name']
        source_group = kwargs['source_group']

        real_name = take_name_from_list_case_ignore(context, self.file_lists[file_path],
                                                    file_name)
        if real_name:
            name_to_add = real_name
        else:
            name_to_add = file_name
            message(context, 'Adding absent {} file into project files'
                    .format(file_name), 'warn')

        files_container[file_path].append(name_to_add)
        if file_path:
            file_path = file_path + '/'
        file_path_name = file_path + name_to_add
        working_path = os.path.dirname(context.vcxproj_path)
        file_path_name = normalize_path(context, working_path,
                                        file_path_name,
                                        False)
        if source_group not in context.source_groups:
            context.source_groups[source_group] = []
        context.source_groups[source_group].append(file_path_name)
        context.source_groups[source_group].sort(key=str.lower)
        if real_name:
            self.include_directive_case_check(context,
                                              file_path_name,
                                              self.file_lists_for_include_paths)
        context.file_contexts[file_path_name] = self.__create_file_context(context)
        return context.file_contexts[file_path_name]

    def add_file_from_node(self, context, **kwargs):
        """
        Adds file into source group and creates file context using into from xml node
        """
        files_container = kwargs['files_container']
        file_node = kwargs['file_node']
        file_node_attr = kwargs['file_node_attr']
        source_group = kwargs['source_group']

        if file_node.get(file_node_attr) is not None:
            node_text = str(file_node.get(file_node_attr))
            if not node_text.rpartition('.')[-1] in self.languages:
                self.languages.append(node_text.rpartition('.')[-1])
            file_path, file_name = os.path.split(node_text)
            if file_path not in self.file_lists:
                vcxproj_dir = os.path.dirname(context.vcxproj_path)
                self.file_lists[file_path] = []
                if os.path.exists(os.path.join(vcxproj_dir, file_path)):
                    self.file_lists[file_path] = os.listdir(os.path.join(vcxproj_dir, file_path))
            if file_path not in files_container:
                files_container[file_path] = []
            if file_name not in files_container[file_path]:
                return self.__add_file_into_container(
                    context,
                    files_container=files_container,
                    file_path=file_path,
                    file_name=file_name,
                    source_group=source_group
                )
        return ''

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
                    abs_include_path = os.path.normpath(os.path.join(vcxproj_dir, include_path))
                    if os.path.exists(abs_include_path):
                        self.file_lists_for_include_paths[abs_include_path]\
                            = set(os.listdir(abs_include_path))

    def apply_files_to_context(self, context):
        """ Analyzes collected set of files and initializes necessary variables """
        has_headers = bool(context.headers)
        context.has_headers = has_headers
        context.has_only_headers = bool(has_headers and not context.sources)
        message(context, "Source files extensions found: {}".format(self.languages), 'INFO')

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
        cmake_file.write(
            'project({}{})\n\n'.format(make_cmake_literal(context, context.project_name), lang)
        )

    @staticmethod
    def get_source_group_var(context, source_group_name):
        """ Evaluates variable from source group name """
        if not source_group_name:
            return 'no_group_source_files'

        source_group_name = source_group_name.replace(' ', '_')
        return make_cmake_literal(context, source_group_name.replace('\\\\', '__'))

    def write_source_groups(self, context, cmake_file):
        """ Writes source groups of project files into CMakwLists.txt """
        write_comment(cmake_file, 'Source groups')

        source_group_list = sorted(context.source_groups)
        for source_group in source_group_list:
            source_group_var = self.get_source_group_var(context, source_group)
            cmake_file.write('set({}\n'.format(source_group_var))
            for src_file in context.source_groups[source_group]:
                fmt = '    "{}"\n'
                if context.file_contexts[src_file].excluded_from_build:
                    fmt = '#' + fmt
                    message(
                        context,
                        "file {} is excluded from build. Written but commented. "
                        "No support in CMake yet.".format(src_file),
                        'warn4'
                    )
                cmake_file.write(fmt.format(src_file))

            cmake_file.write(')\n')
            cmake_file.write(
                'source_group("{}" FILES ${{{}}})\n\n'.format(source_group, source_group_var)
            )

        cmake_file.write('set(ALL_FILES\n')
        for source_group in source_group_list:
            cmake_file.write(
                '    ${{{}}}\n'.format(context.files.get_source_group_var(context, source_group))
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
