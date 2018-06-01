#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017:
#   Matthieu Estrada, ttamalfor@gmail.com
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
        self.sources = {}
        self.headers = {}

    def collects_source_files(self, context):
        """
        Write the project variables in CMakeLists.txt file

        """

        if '.vcxproj' in context.vcxproj_path:
            source_files_nodes = context.vcxproj['tree'].xpath(
                '//ns:ItemGroup/ns:ClCompile', namespaces=context.vcxproj['ns'])
            header_files_nodes = context.vcxproj['tree'].xpath(
                '//ns:ItemGroup/ns:ClInclude', namespaces=context.vcxproj['ns'])
            source_file_attr = 'Include'
        elif '.vfproj' in context.vcxproj_path:
            source_files_nodes = context.vcxproj['tree'].xpath(
                '/VisualStudioProject/Files/Filter/File')
            header_files_nodes = []
            source_file_attr = 'RelativePath'
        else:
            message("Unsupported project type in ProjectFiles class: {0}"
                    .format(context.vcxproj_path), 'ERROR')
            return

        file_lists = {}
        vcxproj_dir = os.path.dirname(context.vcxproj_path)

        # Cpp Dir
        for source_node in source_files_nodes:
            if source_node.get(source_file_attr) is not None:
                source_node_text = str(source_node.get(source_file_attr))
                source_node_text = '/'.join(source_node_text.split('\\'))
                if not source_node_text.rpartition('.')[-1] in self.languages:
                    self.languages.append(source_node_text.rpartition('.')[-1])
                source_path, source_file = os.path.split(source_node_text)
                if source_path not in file_lists:
                    file_lists[source_path] = os.listdir(os.path.join(vcxproj_dir, source_path))
                if source_path not in self.sources:
                    self.sources[source_path] = []
                if source_file not in self.sources[source_path]:
                    real_name = take_name_from_list_case_ignore(file_lists[source_path],
                                                                source_file)
                    if real_name:
                        self.sources[source_path].append(real_name)
        for source_path in self.sources:
            self.sources[source_path].sort(key=str.lower)

        # Headers Dir
        for header_node in header_files_nodes:
            header_node_text = str(header_node.get(source_file_attr))
            header_node_text = '/'.join(header_node_text.split('\\'))
            header_path, header_file = os.path.split(header_node_text)
            if header_path not in file_lists:
                file_lists[header_path] = os.listdir(os.path.join(vcxproj_dir, header_path))
            if header_path not in self.headers:
                self.headers[header_path] = []
            if header_file not in self.headers[header_path]:
                real_name = take_name_from_list_case_ignore(file_lists[header_path], header_file)
                if real_name:
                    self.headers[header_path].append(real_name)
        for header_path in self.headers:
            self.headers[header_path].sort(key=str.lower)

        has_headers = True if header_files_nodes else False
        context.has_headers = has_headers
        context.has_only_headers = True if has_headers and not source_files_nodes else False
        message("Source files extensions found: %s" % self.languages, 'INFO')

    def find_cmake_project_language(self, context):
        """
        Add CMake Project

        """

        cpp_extensions = ['cc', 'cp', 'cxx', 'cpp', 'CPP', 'c++', 'C']

        available_language = {'c': 'C'}
        available_language.update(dict.fromkeys(cpp_extensions, 'CXX'))

        fortran_extensions = ['F90', 'F', 'f90', 'f', 'fi', 'FI']
        available_language.update(dict.fromkeys(fortran_extensions, 'Fortran'))

        files_language = ''
        if self.languages:
            for l in self.languages:
                if l in available_language:
                    files_language = l
                    break
            if 'cpp' in self.languages:  # priority for C++ for mixes with C
                files_language = 'cpp'

        project_language = ''
        if files_language in available_language:
            project_language = available_language[files_language]
        if project_language:
            context.solution_languages.add(project_language)
        context.project_language = project_language

    def write_cmake_project(self, context, cmake_file):
        """
        Write cmake project for given CMake file

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        lang = ''
        if context.project_language:
            lang = ' ' + context.project_language
        cmake_file.write('project(${{PROJECT_NAME}}{0})\n\n'.format(lang))

    def write_header_files(self, context, cmake_file):
        """
        Write header files variables to file() cmake function

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(self.headers) == 0:
            return

        write_comment(cmake_file, 'Header files')
        cmake_file.write('set(HEADERS_FILES\n')

        working_path = os.path.dirname(context.vcxproj_path)
        if '' in self.headers:
            for header_file in self.headers['']:
                cmake_file.write('    {0}\n'.format(normalize_path(working_path, header_file)))

        for headers_dir in self.headers:
            if headers_dir == '':
                continue
            for header_file in self.headers[headers_dir]:
                cmake_file.write('    {0}\n'
                                 .format(normalize_path(working_path,
                                                        os.path.join(headers_dir, header_file))))

        cmake_file.write(')\n')
        cmake_file.write('source_group("Headers" FILES ${HEADERS_FILES})\n\n')

    def write_source_files(self, context, cmake_file):
        """
        Write source files variables to file() cmake function

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        write_comment(cmake_file, 'Source files')
        cmake_file.write('set(SRC_FILES\n')

        working_path = os.path.dirname(context.vcxproj_path)
        if '' in self.sources:
            for src_file in self.sources['']:
                cmake_file.write('    {0}\n'.format(normalize_path(working_path, src_file)))

        for src_dir in self.sources:
            if src_dir == '':
                continue
            for src_file in self.sources[src_dir]:
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
