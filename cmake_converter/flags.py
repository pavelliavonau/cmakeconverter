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
    Flags
    =====
     Manage compilation flags of project
"""

import os

from os import path

from cmake_converter.message import send
from cmake_converter.data_files import get_propertygroup, get_definitiongroup

cl_flags = 'cl_flags'
defines = 'defines'


class Flags(object):
    """
        Class who check and create compilation flags
    """

    available_std = ['c++11', 'c++14', 'c++17']

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.propertygroup = {}
        self.definitiongroups = {}
        self.std = data['std']
        self.settings = {}

    def define_settings(self):
        """
        Define the settings of vcxproj

        """

        configuration_nodes = self.tree.xpath('//ns:ProjectConfiguration', namespaces=self.ns)
        if configuration_nodes:
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Include'))
                self.settings[configuration_data] = {defines: '', cl_flags: ''}

    def write_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """

        self.cmake.write(
            '################# Flags ################\n'
            '# Defines Flags for Windows and Linux. #\n'
            '########################################\n\n'
        )

        self.define_group_properties()
        self.define_windows_flags()
        self.define_defines()
        self.define_linux_flags()

    def define_linux_flags(self):
        """
        Define the Flags for Linux platforms

        """

        if self.std:
            if self.std in self.available_std:
                send('Cmake will use C++ std %s.' % self.std, 'info')
                linux_flags = '-std=%s' % self.std
            else:
                send(
                    'C++ std %s version does not exist. CMake will use "c++11" instead' % self.std,
                    'warn'
                )
                linux_flags = '-std=c++11'
        else:
            send('No C++ std version specified. CMake will use "c++11" by default.', 'info')
            linux_flags = '-std=c++11'
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            for ref in references:
                reference = str(ref.get('Include'))
                if '\\' in reference:
                    reference = reference.replace('\\', '/')
                lib = os.path.splitext(path.basename(reference))[0]

                if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
                    linux_flags += ' -fPIC'

        self.cmake.write('if(NOT MSVC)\n')
        self.cmake.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} %s")\n' % linux_flags)
        self.cmake.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        self.cmake.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        self.cmake.write('   endif()\n')
        self.cmake.write('endif(NOT MSVC)\n\n')

    def define_group_properties(self):
        """
        Define the PropertyGroups and DefinitionGroups of XML properties

        """

        for setting in self.settings:
            self.propertygroup[setting] = get_propertygroup(
                setting, ' and @Label="Configuration"')

        # ItemDefinitionGroup
        for setting in self.settings:
            self.definitiongroups[setting] = get_definitiongroup(setting)

    def define_defines(self):
        """
        DEFINES
        """

        # PreprocessorDefinitions
        for setting in self.settings:
            define = self.tree.find(
                '%s/ns:ClCompile/ns:PreprocessorDefinitions' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if define is not None:
                for preproc in define.text.split(";"):
                    if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                        self.settings[setting][defines] += '   -D%s \n' % preproc
                # Unicode
                unicode = self.tree.find(
                    "{0}/ns:CharacterSet".format(self.definitiongroups[setting]), namespaces=self.ns
                )
                if unicode is not None:
                    if 'Unicode' in unicode.text:
                        self.settings[setting][defines] += '   -DUNICODE\n'
                        self.settings[setting][defines] += '   -D_UNICODE\n'
                send('PreprocessorDefinitions for {0}'.format(setting), 'ok')

    def define_windows_flags(self):
        """
        Define the Flags for Win32 platforms

        """

        # Define FLAGS for Windows
        self.set_warning_level()
        self.set_whole_program_optimization()
        self.set_use_debug_libraries()
        self.set_runtime_library()
        self.set_optimization()
        self.set_intrinsic_functions()
        self.set_runtime_type_info()
        self.set_function_level_linking()
        self.set_generate_debug_information()
        self.set_exception_handling()

    def set_warning_level(self):
        """
        Set Warning level for Windows: /W

        """

        try:
            warning = self.tree.xpath('//ns:WarningLevel', namespaces=self.ns)[0]
        except IndexError:
            return

        if warning.text != '':
            lvl = ' /W' + warning.text[-1:]
            for setting in self.settings:
                self.settings[setting][cl_flags] += lvl
            send('Warning : ' + warning.text, 'ok')
        else:  # pragma: no cover
            send('No Warning level.', '')

    def set_whole_program_optimization(self):
        """
        Set Whole Program Optimization flag: /GL

        """

        # WholeProgramOptimization
        for setting in self.settings:
            gl = self.tree.xpath(
                '%s/ns:WholeProgramOptimization' % self.propertygroup[setting],
                namespaces=self.ns)
            if gl:
                if 'true' in gl[0].text:
                    self.settings[setting][cl_flags] += ' /GL'
                    send('WholeProgramOptimization for {0}'.format(setting), 'ok')
            else:
                send('No WholeProgramOptimization for {0}'.format(setting), '')

    def set_use_debug_libraries(self):
        """
        Set Use Debug Libraries flag: /MD

        """
        for setting in self.settings:
            md = self.tree.xpath(
                '%s/ns:UseDebugLibraries' % self.propertygroup[setting],
                namespaces=self.ns
            )
            if md:
                if 'true' in md[0].text:
                    self.settings[setting][cl_flags] += ' /MD'
                    send('UseDebugLibrairies for {0}'.format(setting), 'ok')
            else:
                send('No UseDebugLibrairies for {0}'.format(setting), '')

    def set_runtime_library(self):
        """
        Set RuntimeLibrary flag: /MDd

        """

        # RuntimeLibrary
        for setting in self.settings:
            mdd = self.tree.find(
                '%s/ns:ClCompile/ns:RuntimeLibrary' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if mdd is not None:
                if 'MultiThreadedDebugDLL' in mdd.text:
                    self.settings[setting][cl_flags] += ' /MDd'
                    send('RuntimeLibrary for {0}'.format(setting), 'ok')
            else:
                send('No RuntimeLibrary for {0}'.format(setting), '')

    def set_optimization(self):
        """
        Set Optimization flag: /Od

        """

        for setting in self.settings:
            opt = self.tree.find(
                '%s/ns:ClCompile/ns:Optimization' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if opt is not None:
                if 'Disabled' in opt.text:
                    self.settings[setting][cl_flags] += ' /Od'
                    send('Optimization for {0}'.format(setting), 'ok')
            else:
                send('No Optimization for {0}'.format(setting), '')

    def set_intrinsic_functions(self):
        """
        Set Intrinsic Functions flag: /Oi

        """

        for setting in self.settings:
            oi = self.tree.find(
                '%s/ns:ClCompile/ns:IntrinsicFunctions' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if oi is not None:
                if 'true' in oi.text:
                    self.settings[setting][cl_flags] += ' /Oi'
                    send('IntrinsicFunctions for {0}'.format(setting), 'ok')
            else:
                send('No IntrinsicFunctions for {0}'.format(setting), '')

    def set_runtime_type_info(self):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        # RuntimeTypeInfo
        for setting in self.settings:
            gr = self.tree.find(
                '%s/ns:ClCompile/ns:RuntimeTypeInfo' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if gr is not None:
                if 'true' in gr.text:
                    self.settings[setting][cl_flags] += ' /GR'
                    send('RuntimeTypeInfo for {0}'.format(setting), 'ok')
            else:
                send('No RuntimeTypeInfo for {0}'.format(setting), '')

    def set_function_level_linking(self):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        for setting in self.settings:
            gy = self.tree.find(
                '%s/ns:ClCompile/ns:FunctionLevelLinking' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if gy is not None:
                if 'true' in gy.text:
                    self.settings[setting][cl_flags] += ' /Gy'
                    send('FunctionLevelLinking for {0}'.format(setting), 'ok')
            else:
                send('No FunctionLevelLinking for {0}'.format(setting), '')

    def set_generate_debug_information(self):
        """
        Set GenerateDebugInformation flag: /Zi

        """

        for setting in self.settings:
            zi = self.tree.find(
                '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if zi is not None:
                if 'true' in zi.text:
                    self.settings[setting][cl_flags] += ' /Zi'
                    send('GenerateDebugInformation for {0}'.format(setting), 'ok')
            else:
                send('No GenerateDebugInformation for {0}'.format(setting), '')

    def set_exception_handling(self):
        """
        Set ExceptionHandling flag: /EHsc

        """

        for setting in self.settings:
            ehs = self.tree.find(
                '%s/ns:ClCompile/ns:ExceptionHandling' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if ehs is not None:
                if 'false' in ehs.text:
                    send('No ExceptionHandling for {0}'.format(setting), '')
            else:
                self.settings[setting][cl_flags] += ' /EHsc'
                send('ExceptionHandling for {0}'.format(setting), 'ok')

    def write_defines_and_flags(self):
        """
        Get and write Preprocessor Macros definitions

        """
        cmake = self.cmake

        cmake.write('\n# Preprocessor definitions\n')
        for setting in self.settings:
            conf = setting.split('|')[0].upper()
            cmake.write('\nif(CMAKE_BUILD_TYPE STREQUAL {0}_BUILD_TYPE)\n'.format(conf))
            cmake.write(
                '    target_compile_definitions(${{PROJECT_NAME}} PRIVATE \n{0}    )'.format(
                    self.settings[setting][defines])
            )
            cmake.write('\n    if(MSVC)')
            cmake.write(
                '\n        target_compile_options(${{PROJECT_NAME}} PRIVATE {0})'.format(
                    self.settings[setting][cl_flags])
            )
            cmake.write('\n    endif()\n')
            cmake.write('\nendif()\n')
