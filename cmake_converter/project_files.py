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

from cmake_converter.message import send


class ProjectFiles(object):
    """
        Class who collect and store project files
    """

    c_folder_nb = 1
    h_folder_nb = 1

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.cppfiles = self.tree.xpath('//ns:ClCompile', namespaces=self.ns)
        self.headerfiles = self.tree.xpath('//ns:ClInclude', namespaces=self.ns)
        self.language = []

    def write_files_variables(self):
        """
        Write the project variables in CMakeLists.txt file

        """

        # Cpp Dir
        known_cpp = []
        ProjectFiles.c_folder_nb = 1
        self.cmake.write('# Folders files\n')
        for cpp in self.cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                if not cxx.rpartition('.')[-1] in self.language:
                    self.language.append(cxx.rpartition('.')[-1])
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in known_cpp:
                    if not current_cpp:
                        # Case files are beside the VS Project
                        current_cpp = './'
                    known_cpp.append(current_cpp)
                    self.cmake.write(
                        'set(CPP_DIR_%s %s)\n' % (str(ProjectFiles.c_folder_nb), current_cpp)
                    )
                    ProjectFiles.c_folder_nb += 1

        # Headers Dir
        known_headers = []
        ProjectFiles.h_folder_nb = 1
        for header in self.headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in known_headers:
                known_headers.append(current_header)
                self.cmake.write(
                    'set(HEADER_DIR_%s %s)\n' % (str(ProjectFiles.h_folder_nb), current_header)
                )
                ProjectFiles.h_folder_nb += 1

        send("C++ Extensions found: %s" % self.language, 'INFO')

    def write_source_files(self):
        """
        Write source files variables to file() cmake function

        """

        self.cmake.write('################ Files ################\n'
                         '#   --   Add files to project.   --   #\n'
                         '#######################################\n\n')
        self.cmake.write('file(GLOB SRC_FILES\n')
        c = 1
        while c < ProjectFiles.c_folder_nb:
            for lang in self.language:
                self.cmake.write('    ${CPP_DIR_' + str(c) + '}/*.%s\n' % lang)
            c += 1
        h = 1
        while h < ProjectFiles.h_folder_nb:
            self.cmake.write('    ${HEADER_DIR_' + str(h) + '}/*.h\n')
            h += 1
        self.cmake.write(')\n\n')

    def add_additional_code(self, file_to_add):
        """
        Add additional file with CMake code inside

        :param file_to_add: the file who contains CMake code
        :type file_to_add: str
        """

        if file_to_add != '':
            try:
                fc = open(file_to_add, 'r')
                self.cmake.write('############# Additional Code #############\n')
                self.cmake.write('# Provides from external file.            #\n')
                self.cmake.write('###########################################\n\n')
                for line in fc:
                    self.cmake.write(line)
                fc.close()
                self.cmake.write('\n')
                send('File of Code is added = ' + file_to_add, 'warn')
            except OSError as e:
                send(str(e), 'error')
                send(
                    'Wrong data file ! Code was not added, please verify file name or path !',
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
            send('CMake will build a SHARED Library.', '')
        elif configurationtype.text == 'StaticLibrary':  # pragma: no cover
            self.cmake.write('# Add library to build.\n')
            self.cmake.write('add_library(${PROJECT_NAME} STATIC\n')
            send('CMake will build a STATIC Library.', '')
        else:  # pragma: no cover
            self.cmake.write('# Add executable to build.\n')
            self.cmake.write('add_executable(${PROJECT_NAME} \n')
            send('CMake will build an EXECUTABLE.', '')
        self.cmake.write('   ${SRC_FILES}\n')
        self.cmake.write(')\n\n')
