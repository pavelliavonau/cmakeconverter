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

from cmake_converter.message import send
from cmake_converter.data_files import get_propertygroup


class ProjectVariables(object):
    """
        Class who defines all the CMake variables to be used by the project
    """

    out_deb = False
    out_rel = False

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.output = data['cmake_output']
        self.vs_outputs = {
            'debug': {
                'x86': None,
                'x64': None
            },
            'release': {
                'x86': None,
                'x64': None
            }
        }

    def add_project_variables(self):
        """
        Add main CMake project variables

        """

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

        # PropertyGroup TODO: remove hard code
        # return
        # prop_deb_x86 = get_propertygroup('debug', 'x86')
        # prop_deb_x64 = get_propertygroup('debug', 'x64')
        # prop_rel_x86 = get_propertygroup('release', 'x86')
        # prop_rel_x64 = get_propertygroup('release', 'x64')
        #
        # if not self.vs_outputs['debug']['x86']:
        #     self.vs_outputs['debug']['x86'] = self.tree.find(
        #         '%s//ns:OutDir' % prop_deb_x86, namespaces=self.ns
        #     )
        #     if self.vs_outputs['debug']['x86'] is None:
        #         vs_output_debug_x86 = self.tree.xpath(
        #             '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns
        #         )
        #         if vs_output_debug_x86:
        #             self.vs_outputs['debug']['x86'] = vs_output_debug_x86[0]
        # if not self.vs_outputs['debug']['x64']:
        #     self.vs_outputs['debug']['x64'] = self.tree.find(
        #         '%s/ns:OutDir' % prop_deb_x64, namespaces=self.ns
        #     )
        #     if self.vs_outputs['debug']['x64'] is None:
        #         vs_output_debug_x64 = self.tree.xpath(
        #             '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns
        #         )
        #         if vs_output_debug_x64:
        #             self.vs_outputs['debug']['x64'] = vs_output_debug_x64[0]
        # if not self.vs_outputs['release']['x86']:
        #     self.vs_outputs['release']['x86'] = self.tree.find(
        #         '%s//ns:OutDir' % prop_rel_x86, namespaces=self.ns
        #     )
        #     if self.vs_outputs['release']['x86'] is None:
        #         vs_output_release_x86 = self.tree.xpath(
        #             '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns
        #         )
        #         if vs_output_release_x86:
        #             self.vs_outputs['release']['x86'] = vs_output_release_x86[0]
        # if not self.vs_outputs['release']['x64']:
        #     self.vs_outputs['release']['x64'] = self.tree.find(
        #         '%s//ns:OutDir' % prop_rel_x64, namespaces=self.ns
        #     )
        #     if self.vs_outputs['release']['x64'] is None:
        #         vs_output_release_x64 = self.tree.xpath(
        #             '//ns:PropertyGroup[@Label="UserMacros"]/ns:OutDir', namespaces=self.ns
        #         )
        #         if vs_output_release_x64:
        #             self.vs_outputs['release']['x64'] = vs_output_release_x64[0]

    def add_outputs_variables(self):
        """
        Add Outputs Variables

        """

        output_deb_x86 = ''
        output_deb_x64 = ''
        output_rel_x86 = ''
        output_rel_x64 = ''

        if not self.output:
            if self.vs_outputs['debug']['x86'] is not None:
                output_deb_x86 = self.cleaning_output(self.vs_outputs['debug']['x86'].text)
            if self.vs_outputs['debug']['x64'] is not None:
                output_deb_x64 = self.cleaning_output(self.vs_outputs['debug']['x64'].text)
            if self.vs_outputs['release']['x86'] is not None:
                output_rel_x86 = self.cleaning_output(self.vs_outputs['release']['x86'].text)
            if self.vs_outputs['release']['x64'] is not None:
                output_rel_x64 = self.cleaning_output(self.vs_outputs['release']['x64'].text)
        else:
            if self.output[-1:] == '/' or self.output[-1:] == '\\':
                build_type = '${CMAKE_BUILD_TYPE}'
            else:
                build_type = '/${CMAKE_BUILD_TYPE}'
            output_deb_x86 = self.output + build_type
            output_deb_x64 = self.output + build_type
            output_rel_x86 = self.output + build_type
            output_rel_x64 = self.output + build_type

        output_deb_x86 = output_deb_x86.strip().replace('\n', '')
        output_deb_x64 = output_deb_x64.strip().replace('\n', '')
        output_rel_x86 = output_rel_x86.strip().replace('\n', '')
        output_rel_x64 = output_rel_x64.strip().replace('\n', '')

        self.cmake.write('# Output Variables\n')
        if output_deb_x64 or output_deb_x86:
            debug_output = output_deb_x64 if output_deb_x64 else output_deb_x86
            send('Output Debug = %s' % debug_output, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG ' + debug_output + ')\n')
            ProjectVariables.out_deb = True
        else:  # pragma: no cover
            send('No Output Debug found. Use [Debug/bin] by default !', 'warn')
            self.cmake.write('set(OUTPUT_DEBUG Debug/bin)\n')
            ProjectVariables.out_deb = True

        if output_rel_x64 or output_rel_x86:
            release_output = output_rel_x64 if output_rel_x64 else output_rel_x86
            send('Output Release = ' + release_output, 'ok')
            self.cmake.write('set(OUTPUT_REL ' + release_output + ')\n')
            ProjectVariables.out_rel = True
        else:  # pragma: no cover
            send('No Output Release found. Use [Release/bin] by default !', 'warn')
            self.cmake.write('set(OUTPUT_RELEASE Release/bin)\n')
            ProjectVariables.out_rel = True

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
            '$(SolutionDir)', '$(Platform)', '$(Configuration)', '$(ProjectDir)'
        ]
        output = output.replace('\\', '/')
        split_output = output.split('/')

        for var in variables_to_remove:
            if var in split_output:
                split_output.remove(var)

        final_output = '/'.join(split_output)

        # Case path is relative
        for var in variables_to_remove:
            if '%s..' % var in final_output:
                final_output = final_output.replace('%s..' % var, '..')

        return final_output

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
        self.cmake.write(
            '############## CMake Project ################\n'
            '#        The main options of project        #\n'
            '#############################################\n\n'
        )
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
            send('No Output found or define. CMake will use current directory as output !', 'warn')
