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
    ProjectVariables
    ================
     Manage creation of CMake variables that will be used during compilation
"""

import os
import ntpath

from cmake_converter.utils import message, get_title
from cmake_converter.data_files import get_propertygroup


class ProjectVariables(object):
    """
        Class who defines all the CMake variables to be used by the project
    """

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.output = data['cmakeoutput']
        self.dependencies = data['dependencies']
        self.cmake_outputs = {}
        self.configurations = []

    def add_project_variables(self):  # pylint: disable=too-many-locals
        """
        Add main CMake project variables

        """

        # Project Name
        title = get_title('Variables', 'Change if you want modify path or other values')
        self.cmake.write(title)

        root_projectname = self.tree.xpath('//ns:RootNamespace', namespaces=self.ns)
        project = False
        self.cmake.write('# Project name\n')
        if root_projectname:
            projectname = root_projectname[0]
            if projectname.text:
                self.cmake.write('set(PROJECT_NAME ' + projectname.text + ')\n\n')
                project = True
        if not project:  # pragma: no cover
            self.cmake.write('set(PROJECT_NAME <PLEASE SET YOUR PROJECT NAME !!>)\n\n')
            message(
                'No PROJECT NAME found or define. '
                'Please set [PROJECT_NAME] variable in CMakeLists.txt.',
                'error'
            )

        self.add_dependencies_variables()
        self.add_output_variables()

    def add_dependencies_variables(self):
        """
        Add dependencies variables

        """

        if not self.dependencies:
            references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
            if references:
                self.cmake.write('# Dependencies\n')
                for ref in references:
                    reference = str(ref.get('Include'))
                    path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                    self.cmake.write(
                        'set(%s_DIR %s)\n' % (
                            path_to_reference.upper(),
                            reference.replace('\\', '/').replace('.vcxproj', ''))
                    )
            self.cmake.write('\n')

    def add_output_variables(self):
        """
        Add output variables

        """

        if not self.output:
            # Get configurations
            configuration_nodes = self.tree.xpath('//ns:ProjectConfiguration', namespaces=self.ns)
            target_plaforms = []
            if configuration_nodes:
                for configuration_node in configuration_nodes:
                    configuration_data = str(configuration_node.get('Include'))
                    target_plaforms.append(configuration_data)

            for target_platform in target_plaforms:
                property_grp = get_propertygroup(target_platform)
                output = self.tree.find(
                    '%s//ns:OutDir' % property_grp, namespaces=self.ns
                )
                if output is not None:
                    output = output.text.replace('$(ProjectDir)', '').replace('\\', '/')
                    output = self.cleaning_output(output)
                    self.cmake_outputs[target_platform] = output
        else:
            # Remove slash/backslash if needed
            if self.output.endswith('/') or self.output.endswith('\\'):
                self.output = self.output[0:-1]
            # Define only output for x64
            self.cmake_outputs['Debug|x64'] = '/'.join([self.output, '${CMAKE_BUILD_TYPE}'])
            self.cmake_outputs['Release|x64'] = '/'.join([self.output, '${CMAKE_BUILD_TYPE}'])

        output_debug = ''
        output_release = ''

        for output in self.cmake_outputs:
            if 'Debug' in output:
                if 'x64' in output:
                    output_debug = self.cmake_outputs[output]
                if 'Win32' in output and not output_debug:
                    output_debug = self.cmake_outputs[output]
            if 'Release' in output:
                if 'x64' in output:
                    output_release = self.cmake_outputs[output]
                if 'Win32' in output and not output_release:
                    output_release = self.cmake_outputs[output]

        # In case converter can't find output, assign default
        if not output_debug:
            output_debug = '${CMAKE_BUILD_TYPE}/bin'
        if not output_release:
            output_release = '${CMAKE_BUILD_TYPE}/bin'

        self.cmake.write('# Outputs\n')
        self.cmake.write('set(OUTPUT_DEBUG %s)\n' % output_debug)
        self.cmake.write('set(OUTPUT_RELEASE %s)\n' % output_release)

        message('Following output define for Release: %s' % output_release, 'INFO')
        message('Following output define for Debug: %s' % output_debug, 'INFO')

    @staticmethod
    def cleaning_output(output):
        """
        Clean Output string by remove VS Project Variables

        :param output: Output to clean
        :type output: str
        :return: clean output
        :rtype: str
        """

        variables_to_remove = [
            '$(SolutionDir)', '$(Platform)', '$(Configuration)', '$(ProjectDir)', '$(SolutionName)',
        ]
        slash_to_remove = ['/-/', '/_/', '//']
        output = output.replace('\\', '/')

        for var in variables_to_remove:
            output = output.replace(var, '')
        for slash in slash_to_remove:
            output = output.replace(slash, '/')

        if output == '/':
            output = './'

        return output

    def add_cmake_project(self, language):
        """
        Add CMake Project

        :param language: type of project language: cpp | c
        :type language: list
        """

        cpp_extensions = ['cc', 'cp', 'cxx', 'cpp', 'CPP', 'c++', 'C']

        available_language = {'c': 'C'}
        available_language.update(dict.fromkeys(cpp_extensions, 'CXX'))

        self.cmake.write('\n')
        title = get_title('CMake Project', 'The main options of project')
        self.cmake.write(title)
        lang = 'cpp'
        if len(language) is not 0:
            lang = language[0]
        self.cmake.write('project(${PROJECT_NAME} %s)\n\n' % available_language[lang].upper())

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

    def add_cmake_output_directories(self):
        """
        Add output directory for each artefacts CMake target

        """

        title = get_title('Artefacts Output', 'Defines outputs , depending BUILD TYPE')
        self.cmake.write(title)

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
