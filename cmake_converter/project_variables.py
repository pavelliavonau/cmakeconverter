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
    Project Variables manage creation of CMake variables that will be used during compilation
"""
from cmake_converter.message import send
from cmake_converter.data_files import get_propertygroup


class ProjectVariables(object):
    """
        Class who defines all the CMake variables to be used by the project
    """

    out_deb_x86 = None
    out_deb_x64 = None
    out_rel_x86 = None
    out_rel_x64 = None
    out_deb = False
    out_rel = False

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.output = data['cmake_output']

    def add_project_variables(self):
        """
        Add main CMake project variables

        """

        # PropertyGroup
        prop_deb_x86 = get_propertygroup('debug', 'x86')
        prop_deb_x64 = get_propertygroup('debug', 'x64')
        prop_rel_x86 = get_propertygroup('release', 'x86')
        prop_rel_x64 = get_propertygroup('release', 'x64')

        ProjectVariables.out_deb_x86 = self.tree.find(
            '%s/ns:OutDir' % prop_deb_x86, namespaces=self.ns
        )
        if ProjectVariables.out_deb_x86 is None:
            ProjectVariables.out_deb_x86 = self.tree.find(prop_deb_x86, namespaces=self.ns)

        ProjectVariables.out_deb_x64 = self.tree.find(
            '%s/ns:OutDir' % prop_deb_x64, namespaces=self.ns
        )
        if ProjectVariables.out_deb_x64 is None:
            ProjectVariables.out_deb_x64 = self.tree.find(prop_deb_x64, namespaces=self.ns)

        ProjectVariables.out_rel_x86 = self.tree.find(
            '%s/ns:OutDir' % prop_rel_x86, namespaces=self.ns
        )
        if ProjectVariables.out_rel_x86 is None:
            ProjectVariables.out_rel_x86 = self.tree.find(prop_rel_x86, namespaces=self.ns)

        ProjectVariables.out_rel_x64 = self.tree.find(
            '%s/ns:OutDir' % prop_rel_x64, namespaces=self.ns
        )
        if ProjectVariables.out_rel_x64 is None:
            ProjectVariables.out_rel_x64 = self.tree.find(prop_rel_x64, namespaces=self.ns)

        # CMake Minimum required.
        self.cmake.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

        # Project Name
        self.cmake.write(
            '################### Variables. ####################\n'
            '# Change if you want modify path or other values. #\n'
            '###################################################\n\n'
        )
        root_projectname = self.tree.xpath('//ns:RootNamespace', namespaces=self.ns)
        project = False
        if root_projectname:
            projectname = root_projectname[0]
            if projectname.text:
                self.cmake.write('set(PROJECT_NAME ' + projectname.text + ')\n')
                project = True
        if not project:  # pragma: no cover
            self.cmake.write('set(PROJECT_NAME <PLEASE SET YOUR PROJECT NAME !!>)\n')
            send(
                'No PROJECT NAME found or define. '
                'Please set [PROJECT_NAME] variable in CMakeLists.txt.',
                'error'
            )

    def add_outputs_variables(self):
        """
        Add Outputs Variables

        """

        self.cmake.write('# Output Variables\n')
        output_deb_x86 = ''
        output_deb_x64 = ''
        output_rel_x86 = ''
        output_rel_x64 = ''
        if not self.output:
            if ProjectVariables.out_deb_x86 is not None:
                output_deb_x86 = ProjectVariables.out_deb_x86.text.replace(
                    '$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_deb_x64 is not None:
                output_deb_x64 = ProjectVariables.out_deb_x64.text.replace(
                    '$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_rel_x86 is not None:
                output_rel_x86 = ProjectVariables.out_rel_x86.text.replace(
                    '$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_rel_x64 is not None:
                output_rel_x64 = ProjectVariables.out_rel_x64.text.replace(
                    '$(ProjectDir)', '').replace('\\', '/')
        else:
            if self.output[-1:] == '/' or self.output[-1:] == '\\':
                build_type = '${CMAKE_BUILD_TYPE}'
            else:
                build_type = '/${CMAKE_BUILD_TYPE}'
            output_deb_x86 = self.output + build_type
            output_deb_x64 = self.output + build_type
            output_rel_x86 = self.output + build_type
            output_rel_x64 = self.output + build_type

        if output_deb_x64 != '':
            send('Output Debug = ' + output_deb_x64, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG ' + output_deb_x64 + ')\n')
            ProjectVariables.out_deb = True
        elif output_deb_x86 != '':  # pragma: no cover
            send('Output Debug = ' + output_deb_x86, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG ' + output_deb_x86 + ')\n')
            ProjectVariables.out_deb = True
        else:  # pragma: no cover
            send('No Output Debug define.', '')

        if output_rel_x64 != '':
            send('Output Release = ' + output_rel_x64, 'ok')
            self.cmake.write('set(OUTPUT_REL ' + output_rel_x64 + ')\n')
            ProjectVariables.out_rel = True
        elif output_rel_x86 != '':  # pragma: no cover
            send('Output Release = ' + output_rel_x86, 'ok')
            self.cmake.write('set(OUTPUT_REL ' + output_rel_x86 + ')\n')
            ProjectVariables.out_rel = True
        else:  # pragma: no cover
            send('No Output Release define.', '')

    def add_cmake_project(self):
        """
        Add CMake Project

        """

        self.cmake.write('\n')
        self.cmake.write(
            '############## CMake Project ################\n'
            '#        The main options of project        #\n'
            '#############################################\n\n'
        )
        self.cmake.write('project(${PROJECT_NAME} CXX)\n\n')

    def add_default_target(self):
        """
        Add default target release if not define.

        """

        self.cmake.write(
            '# Define Release by default.\n'
            'if(NOT CMAKE_BUILD_TYPE)\n'
            '  set(CMAKE_BUILD_TYPE "Release")\n'
            '  message(STATUS "Build type not specified: Use Release by default.")\n'
            'endif(NOT CMAKE_BUILD_TYPE)\n\n'
        )

    def add_artefact_target_outputs(self):
        """
        Add outputs for each artefacts CMake target

        """

        if ProjectVariables.out_deb or ProjectVariables.out_rel:
            self.cmake.write('############## Artefacts Output #################\n')
            self.cmake.write('# Defines outputs , depending Debug or Release. #\n')
            self.cmake.write('#################################################\n\n')
            if ProjectVariables.out_deb:
                self.cmake.write('if(CMAKE_BUILD_TYPE STREQUAL "Debug")\n')
                self.cmake.write(
                    '  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")\n'
                )
                self.cmake.write(
                    '  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")\n'
                )
                self.cmake.write(
                    '  set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")'
                    '\n'
                )
            if ProjectVariables.out_rel:
                self.cmake.write('else()\n')
                self.cmake.write(
                    '  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n'
                )
                self.cmake.write(
                    '  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n'
                )
                self.cmake.write(
                    '  set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n'
                )
                self.cmake.write('endif()\n\n')
        else:  # pragma: no cover
            send('No Output found or define. CMake will use default ouputs.', 'warn')
