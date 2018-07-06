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

    def get_source_files_descriptors(self, context):
        return []

    def parse_file_node_options(self, context, file_node, node_text):
        pass

    def __get_info_from_file_nodes(self, context, descriptor, file_lists):
        """

        """

        context_files = descriptor[0]
        files_nodes = descriptor[1]
        file_node_attr = descriptor[2]

        vcxproj_dir = os.path.dirname(context.vcxproj_path)

        for file_node in files_nodes:
            if file_node.get(file_node_attr) is not None:
                node_text = str(file_node.get(file_node_attr))
                node_text = '/'.join(node_text.split('\\'))
                if not node_text.rpartition('.')[-1] in self.languages:
                    self.languages.append(node_text.rpartition('.')[-1])
                file_path, file_name = os.path.split(node_text)
                if file_path not in file_lists:
                    file_lists[file_path] = os.listdir(os.path.join(vcxproj_dir, file_path))
                if file_path not in context_files:
                    context_files[file_path] = []
                if file_name not in context_files[file_path]:
                    real_name = take_name_from_list_case_ignore(file_lists[file_path],
                                                                file_name)
                    if real_name:
                        context_files[file_path].append(real_name)
                    self.parse_file_node_options(context, file_node, real_name)
        for file_path in context_files:
            context_files[file_path].sort(key=str.lower)

    def collects_source_files(self, context):
        """
        Write the project variables in CMakeLists.txt file

        """

        file_lists = {}

        descriptors = self.get_source_files_descriptors(context)

        for descriptor in descriptors:
            self.__get_info_from_file_nodes(
                context,
                descriptor,
                file_lists
            )

        has_headers = True if context.headers else False
        context.has_headers = has_headers
        context.has_only_headers = True if has_headers and not context.sources else False
        message("Source files extensions found: {0}".format(self.languages), 'INFO')

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
                'No PROJECT NAME found or define. '
                'Check it!!',
                'error'
            )
        cmake_file.write('project({0}{1})\n\n'.format(context.project_name, lang))

    @staticmethod
    def write_header_files(context, cmake_file):
        """
        Write header files variables to file() cmake function

        :param context: Converter context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(context.headers) == 0:
            return

        write_comment(cmake_file, 'Header files')
        cmake_file.write('set(HEADERS_FILES\n')

        working_path = os.path.dirname(context.vcxproj_path)
        if '' in context.headers:
            for header_file in context.headers['']:
                cmake_file.write('    {0}\n'.format(normalize_path(working_path, header_file)))

        for headers_dir in context.headers:
            if headers_dir == '':
                continue
            for header_file in context.headers[headers_dir]:
                cmake_file.write('    {0}\n'
                                 .format(normalize_path(working_path,
                                                        os.path.join(headers_dir, header_file))))

        cmake_file.write(')\n')
        cmake_file.write('source_group("Headers" FILES ${HEADERS_FILES})\n\n')

    @staticmethod
    def write_source_files(context, cmake_file):
        """
        Write source files variables to file() cmake function

        :param context: Converter context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        write_comment(cmake_file, 'Source files')
        cmake_file.write('set(SRC_FILES\n')

        working_path = os.path.dirname(context.vcxproj_path)
        if '' in context.sources:
            for src_file in context.sources['']:
                cmake_file.write('    {0}\n'.format(normalize_path(working_path, src_file)))

        for src_dir in context.sources:
            if src_dir == '':
                continue
            for src_file in context.sources[src_dir]:
                cmake_file.write('    {0}\n'
                                 .format(normalize_path(working_path,
                                                        os.path.join(src_dir, src_file))))

        cmake_file.write(')\n')
        cmake_file.write('source_group("Sources" FILES ${SRC_FILES})\n\n')

    @staticmethod
    def add_additional_code(file_to_add, cmake_file):
        """
        Add additional file with CMake code inside

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
                message('File of Code is added = ' + file_to_add, 'warn')
            except OSError as e:
                message(str(e), 'error')
                message(
                    'Wrong data file ! Code was not added, please verify file name or path !',
                    'error'
                )
