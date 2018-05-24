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
from cmake_converter.utils import message, write_title


class ProjectFiles(object):
    """
        Class who collect and store project files
    """

    def __init__(self, context):
        self.vcxproj_path = context['vcxproj_path']
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.context = context
        if '.vcxproj' in self.vcxproj_path:
            self.source_files = self.tree.xpath('//ns:ItemGroup/ns:ClCompile', namespaces=self.ns)
            self.header_files = self.tree.xpath('//ns:ItemGroup/ns:ClInclude', namespaces=self.ns)
            self.source_file_attr = 'Include'
        elif '.vfproj' in self.vcxproj_path:
            self.source_files = self.tree.xpath('/VisualStudioProject/Files/Filter/File')
            self.header_files = []
            self.source_file_attr = 'RelativePath'
        else:
            message("Unsupported project type in ProjectFiles class: {0}"
                    .format(self.vcxproj_path), 'ERROR')

        self.language = []
        self.sources = {}
        self.headers = {}

    def collects_source_files(self):
        """
        Write the project variables in CMakeLists.txt file

        """

        filelists = {}
        vcxproj_dir = os.path.dirname(self.vcxproj_path)

        # Cpp Dir
        for cpp in self.source_files:
            if cpp.get(self.source_file_attr) is not None:
                cxx = str(cpp.get(self.source_file_attr))
                cxx = '/'.join(cxx.split('\\'))
                if not cxx.rpartition('.')[-1] in self.language:
                    self.language.append(cxx.rpartition('.')[-1])
                cpp_path, cxx_file = os.path.split(cxx)
                if cpp_path not in filelists:
                    filelists[cpp_path] = os.listdir(os.path.join(vcxproj_dir, cpp_path))
                if cpp_path not in self.sources:
                    self.sources[cpp_path] = []
                if cxx_file not in self.sources[cpp_path]:
                    real_name = take_name_from_list_case_ignore(filelists[cpp_path], cxx_file)
                    if real_name:
                        self.sources[cpp_path].append(real_name)
        for source_path in self.sources:
            self.sources[source_path].sort(key=str.lower)

        # Headers Dir
        for header in self.header_files:
            h = str(header.get(self.source_file_attr))
            h = '/'.join(h.split('\\'))
            header_path, header_file = os.path.split(h)
            if header_path not in filelists:
                filelists[header_path] = os.listdir(os.path.join(vcxproj_dir, header_path))
            if header_path not in self.headers:
                self.headers[header_path] = []
            if header_file not in self.headers[header_path]:
                real_name = take_name_from_list_case_ignore(filelists[header_path], header_file)
                if real_name:
                    self.headers[header_path].append(real_name)
        for header_path in self.headers:
            self.headers[header_path].sort(key=str.lower)

        has_headers = True if self.header_files else False
        self.context['has_headers'] = has_headers
        self.context['has_only_headers'] = True if has_headers and not self.source_files else False
        message("Source files extensions found: %s" % self.language, 'INFO')

    def find_cmake_project_language(self):
        """
        Add CMake Project

        """

        cpp_extensions = ['cc', 'cp', 'cxx', 'cpp', 'CPP', 'c++', 'C']

        available_language = {'c': 'C'}
        available_language.update(dict.fromkeys(cpp_extensions, 'CXX'))

        fortran_extensions = ['F90', 'F', 'f90', 'f', 'fi', 'FI']
        available_language.update(dict.fromkeys(fortran_extensions, 'Fortran'))

        files_language = ''
        if self.language:
            for l in self.language:
                if l in available_language:
                    files_language = l
                    break
            if 'cpp' in self.language:  # priority for C++ for mixes with C
                files_language = 'cpp'

        project_language = ''
        if files_language in available_language:
            project_language = available_language[files_language]
        if project_language:
            self.context['solution_languages'].add(project_language)
        self.context['project_language'] = project_language

    def write_cmake_project(self, cmake_file):
        """
        Write cmake project for given CMake file

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        lang = ''
        if self.context['project_language']:
            lang = ' ' + self.context['project_language']
        cmake_file.write('project(${{PROJECT_NAME}}{0})\n\n'.format(lang))

    def write_header_files(self, cmake_file):
        """
        Write header files variables to file() cmake function

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(self.headers) == 0:
            return

        write_title(cmake_file, 'Header files')
        cmake_file.write('set(HEADERS_FILES\n')

        working_path = os.path.dirname(self.vcxproj_path)
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

    def write_source_files(self, cmake_file):
        """
        Write source files variables to file() cmake function

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        write_title(cmake_file, 'Source files')
        cmake_file.write('set(SRC_FILES\n')

        working_path = os.path.dirname(self.vcxproj_path)
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
                write_title(cmake_file, 'Provides from external file.')
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
