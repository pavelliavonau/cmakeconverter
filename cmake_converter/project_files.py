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

from cmake_converter.utils import message, get_title


class ProjectFiles(object):
    """
        Class who collect and store project files
    """

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.cppfiles = self.tree.xpath('//ns:ClCompile', namespaces=self.ns)
        self.headerfiles = self.tree.xpath('//ns:ClInclude', namespaces=self.ns)
        self.language = []
        self.sources = {}
        self.headers = {}

    def collects_source_files(self):
        """
        Collects the project source files in CMakeLists.txt file

        """

        # Cpp Dir
        for cpp in self.cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                cxx = '/'.join(cxx.split('\\'))
                if not cxx.rpartition('.')[-1] in self.language:
                    self.language.append(cxx.rpartition('.')[-1])
                cpp_path, cxx_file = os.path.split(cxx)
                if not cpp_path:
                    # Case files are beside the VS Project
                    cpp_path = './'
                if cpp_path not in self.sources:
                    self.sources[cpp_path] = []
                if cxx_file not in self.sources[cpp_path]:
                    self.sources[cpp_path].append(cxx_file)

        # Headers Dir
        for header in self.headerfiles:
            h = str(header.get('Include'))
            h = '/'.join(h.split('\\'))
            header_path, header_file = os.path.split(h)
            if header_path not in self.headers:
                self.headers[header_path] = []
            if header_file not in self.headers[header_path]:
                self.headers[header_path].append(header_file)

        message("C++ Extensions found: %s" % self.language, 'INFO')

    def write_source_files(self):
        """
        Write source files variables to file() cmake function

        """

        def add_specific_sources(src_list, condition):  # pragma: no cover
            """
            Add specific sources for platforms
            :param src_list: list of source file
            :type src_list: list
            :param condition: condition to add in "if" statement
            :type condition: str
            """

            self.cmake.write('if(%sMSVC)\n' % condition)
            self.cmake.write('    set(SRC_FILES\n        ${SRC_FILES}\n')
            while src_list:
                self.cmake.write('        %s\n' % src_list.pop())
            self.cmake.write('    )\n')
            self.cmake.write('endif()\n')

        windows_sources = []
        linux_sources = []

        title = get_title('Files & Targets', 'Files of project and target to build')
        self.cmake.write(title)

        self.cmake.write('# Source Files\n')
        self.cmake.write('set(SRC_FILES\n')

        for src_dir in self.sources:
            for src_file in self.sources[src_dir]:
                if src_file in ['crashhandler_windows.cpp', 'stacktrace_windows.cpp']:
                    windows_sources.append(os.path.join(src_dir, src_file))
                    if 'crashhandler_windows.cpp' in src_file:
                        linux_sources.append(
                            os.path.join(src_dir, src_file.replace('windows', 'unix'))
                        )
                else:
                    self.cmake.write('    %s\n' % os.path.join(src_dir, src_file))
        self.cmake.write(')\n')

        # Manage specific sources (Currently only used for g3log)
        if windows_sources:
            add_specific_sources(windows_sources, '')
        if linux_sources:
            add_specific_sources(linux_sources, 'NOT ')

        self.cmake.write('source_group("Sources" FILES ${SRC_FILES})\n\n')

        self.cmake.write('# Header Files\n')
        self.cmake.write('set(HEADERS_FILES\n')

        for hdrs_dir in self.headers:
            for header_file in self.headers[hdrs_dir]:
                self.cmake.write('    %s\n' % os.path.join(hdrs_dir, header_file))

        self.cmake.write(')\n')
        self.cmake.write('source_group("Headers" FILES ${HEADERS_FILES})\n\n')

    def add_include_cmake(self, filename):
        """
        Add include directive for filename

        :param filename: name of file to include
        :type filename: str
        """

        self.cmake.write('include("%s")\n\n' % filename)
        message('File "%s" is included in CMakeLists.txt' % filename, 'warn')

    def add_additional_code(self, filename):
        """
        Add additional file with CMake code inside

        :param filename: the file who contains CMake code
        :type filename: str
        """

        if filename:
            try:
                fc = open(filename)
                title = get_title('Additional Code', 'Provides from an external file')
                self.cmake.write(title)

                for line in fc:
                    self.cmake.write(line)
                fc.close()
                self.cmake.write('\n\n')
                message('File of Code is added = ' + filename, 'warn')
            except OSError as e:
                message(str(e), 'error')
                message(
                    'Wrong data file ! Code was not added, please check given file !',
                    'error'
                )

    def add_target_artefact(self):
        """
        Add Library or Executable target

        """

        configurationtype = self.tree.find('//ns:ConfigurationType', namespaces=self.ns)
        if configurationtype.text == 'DynamicLibrary':
            self.cmake.write('# Add library to build.\n')
            self.cmake.write('add_library(${PROJECT_NAME} SHARED\n')
            message('CMake will build a SHARED Library.', '')
        elif configurationtype.text == 'StaticLibrary':  # pragma: no cover
            self.cmake.write('# Add library to build.\n')
            self.cmake.write('add_library(${PROJECT_NAME} STATIC\n')
            message('CMake will build a STATIC Library.', '')
        else:  # pragma: no cover
            self.cmake.write('# Add executable to build.\n')
            self.cmake.write('add_executable(${PROJECT_NAME} \n')
            message('CMake will build an EXECUTABLE.', '')
        self.cmake.write('   ${SRC_FILES} ${HEADERS_FILES}\n')
        self.cmake.write(')\n\n')
