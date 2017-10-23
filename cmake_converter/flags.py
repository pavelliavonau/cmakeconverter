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
    Flags manage compilation flags of project
"""

from cmake_converter.message import send
from cmake_converter.vsproject import VSProject


class Flags(object):
    """
        Class who check and create compilation flags
    """

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.propertygroup = {
            'debug': {'x86': None, 'x64': None},
            'release': {'x86': None, 'x64': None}
        }
        self.definitiongroups = {
            'debug': {'x86': None, 'x64': None},
            'release': {'x86': None, 'x64': None}
        }
        self.win_deb_flags = ''
        self.win_rel_flags = ''

    def write_flags(self):
        """
        Parse all flags properties and write them in CMakeLists.txt file

        """

        self.cmake.write(
            '################# Flags ################\n'
            '# Defines Flags for Windows and Linux. #\n'
            '########################################\n\n'
        )
        self.define_win_flags()
        self.define_lin_flags()

    def define_lin_flags(self):
        """
        Define the Linux flags

        """

        # Define FLAGS for Linux compiler
        linux_flags = '-std=c++11'
        # TODO recast this part to "set_target_properties" in class: dependencies
        # references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        # if references:
        #     for ref in references:
        #         reference = str(ref.get('Include'))
        #         lib = os.path.splitext(path.basename(reference))[0]
        #         if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
        #             linux_flags += ' -fPIC'

        self.cmake.write('if(NOT MSVC)\n')
        self.cmake.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} %s")\n' % linux_flags)
        self.cmake.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        self.cmake.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        self.cmake.write('   endif()\n')
        self.cmake.write('endif(NOT MSVC)\n\n')

    def define_win_flags(self):
        """
        Write the Win32 flags

        """

        # PropertyGroup
        self.propertygroup['debug']['x86'] = VSProject.get_propertygroup('debug', 'x86')
        self.propertygroup['debug']['x64'] = VSProject.get_propertygroup('debug', 'x64')
        self.propertygroup['release']['x86'] = VSProject.get_propertygroup('release', 'x86')
        self.propertygroup['release']['x64'] = VSProject.get_propertygroup('release', 'x64')

        # ItemDefinitionGroup
        self.definitiongroups['debug']['x86'] = VSProject.get_definitiongroup('debug', 'x86')
        self.definitiongroups['debug']['x64'] = VSProject.get_definitiongroup('debug', 'x64')
        self.definitiongroups['release']['x86'] = VSProject.get_definitiongroup('release', 'x86')
        self.definitiongroups['release']['x64'] = VSProject.get_definitiongroup('release', 'x64')

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

        # Define FLAGS for Windows
        self.cmake.write('if(MSVC)\n')
        if self.win_deb_flags != '':
            send('Debug   FLAGS found = ' + self.win_deb_flags, 'ok')
            self.cmake.write(
                '   set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}%s")\n' % self.win_deb_flags
            )
        else:
            send('No Debug   FLAGS found', '')
        if self.win_rel_flags != '':
            send('Release FLAGS found = ' + self.win_rel_flags, 'ok')
            self.cmake.write(
                '   set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}%s")\n' %
                self.win_rel_flags
            )
        else:
            send('No Release FLAGS found', '')
        self.cmake.write('endif(MSVC)\n')

    def set_warning_level(self):
        """
        Set Warning level for Windows: /W

        """

        warning = self.tree.xpath('//ns:WarningLevel', namespaces=self.ns)[0]
        if warning.text != '':
            lvl = ' /W' + warning.text[-1:]
            self.win_deb_flags += lvl
            self.win_rel_flags += lvl
            send('Warning : ' + warning.text, 'ok')
        else:
            send('No Warning level.', '')

    def set_whole_program_optimization(self):
        """
        Set Whole Program Optimization flag: /GL

        """

        # WholeProgramOptimization
        gl_debug_x86 = self.tree.find(
            '%s/ns:WholeProgramOptimization' % self.propertygroup['debug']['x86'],
            namespaces=self.ns
        )
        gl_debug_x64 = self.tree.find(
            '%s/ns:WholeProgramOptimization' % self.propertygroup['debug']['x64'],
            namespaces=self.ns
        )
        if gl_debug_x86 is not None and gl_debug_x64 is not None:
            if 'true' in gl_debug_x86.text and 'true' in gl_debug_x64.text:
                self.win_deb_flags += ' /GL'
                send('WholeProgramOptimization for Debug', 'ok')
        else:
            send('No WholeProgramOptimization for Debug', '')

        gl_release_x86 = self.tree.find(
            '%s/ns:WholeProgramOptimization' % self.propertygroup['release']['x86'],
            namespaces=self.ns
        )
        gl_release_x64 = self.tree.find(
            '%s/ns:WholeProgramOptimization' % self.propertygroup['release']['x64'],
            namespaces=self.ns
        )
        if gl_release_x86 is not None and gl_release_x64 is not None:
            if 'true' in gl_release_x86.text and 'true' in gl_release_x64.text:
                self.win_rel_flags += ' /GL'
                send('WholeProgramOptimization for Release', 'ok')
        else:
            send('No WholeProgramOptimization for Release', '')

    def set_use_debug_libraries(self):
        """
        Set Use Debug Libraries flag: /MD

        """

        md_debug_x86 = self.tree.find(
            '%s/ns:UseDebugLibraries' % self.propertygroup['debug']['x86'],
            namespaces=self.ns
        )
        md_debug_x64 = self.tree.find(
            '%s/ns:UseDebugLibraries' % self.propertygroup['debug']['x86'],
            namespaces=self.ns
        )
        if md_debug_x64 is not None and md_debug_x86 is not None:
            if 'true' in md_debug_x86.text and 'true' in md_debug_x64.text:
                self.win_deb_flags += ' /MD'
                send('UseDebugLibrairies for Debug', 'ok')
        else:
            send('No UseDebugLibrairies for Debug', '')

        md_release_x86 = self.tree.find(
            '%s/ns:UseDebugLibraries' % self.propertygroup['release']['x86'],
            namespaces=self.ns
        )
        md_release_x64 = self.tree.find(
            '%s/ns:UseDebugLibraries' % self.propertygroup['release']['x64'],
            namespaces=self.ns
        )
        if md_release_x86 is not None and md_release_x64 is not None:
            if 'true' in md_release_x86.text and 'true' in md_release_x64.text:
                self.win_rel_flags += ' /MD'
                send('UseDebugLibrairies for Release', 'ok')
        else:
            send('No UseDebugLibrairies for Release', '')

    def set_runtime_library(self):
        """
        Set RuntimeLibrary flag: /MDd

        """

        # RuntimeLibrary
        mdd_debug_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeLibrary' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        mdd_debug_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeLibrary' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if mdd_debug_x64 is not None and mdd_debug_x86 is not None:
            if 'MultiThreadedDebugDLL' in mdd_debug_x86.text and \
                    'MultiThreadedDebugDLL' in mdd_debug_x64.text:
                self.win_deb_flags += ' /MDd'
                send('RuntimeLibrary for Debug', 'ok')
        else:
            send('No RuntimeLibrary for Debug', '')

        mdd_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeLibrary' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        mdd_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeLibrary' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if mdd_release_x86 is not None and mdd_release_x64 is not None:
            if 'MultiThreadedDebugDLL' in mdd_release_x86.text and \
                    'MultiThreadedDebugDLL' in mdd_release_x64.text:
                self.win_rel_flags += ' /MDd'
                send('RuntimeLibrary for Release', 'ok')
        else:
            send('No RuntimeLibrary for Release', '')

    def set_optimization(self):
        """
        Set Optimization flag: /Od

        """

        opt_debug_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:Optimization' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        opt_debug_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:Optimization' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if opt_debug_x86 is not None and opt_debug_x64 is not None:
            if 'Disabled' in opt_debug_x64.text and 'Disabled' in opt_debug_x86.text:
                self.win_deb_flags += ' /Od'
                send('Optimization for Debug', 'ok')
        else:
            send('No Optimization for Debug', '')

        opt_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:Optimization' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        opt_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:Optimization' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if opt_release_x86 is not None and opt_release_x64 is not None:
            if 'MaxSpeed' in opt_release_x64.text and 'MaxSpeed' in opt_release_x86.text:
                self.win_rel_flags += ' /Od'
                send('Optimization for Release', 'ok')
        else:
            send('No Optimization for Release', '')

    def set_intrinsic_functions(self):
        """
        Set Intrinsic Functions flag: /Oi

        """

        oi_debug_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:IntrinsicFunctions' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        oi_debug_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:IntrinsicFunctions' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if oi_debug_x86 is not None and oi_debug_x64 is not None:
            if 'true' in oi_debug_x86.text and 'true' in oi_debug_x64.text:
                self.win_deb_flags += ' /Oi'
                send('IntrinsicFunctions for Debug', 'ok')
        else:
            send('No IntrinsicFunctions for Debug', '')

        oi_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:IntrinsicFunctions' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        oi_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:IntrinsicFunctions' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if oi_release_x86 is not None and oi_release_x64 is not None:
            if 'true' in oi_release_x86.text and 'true' in oi_release_x64.text:
                self.win_rel_flags += ' /Oi'
                send('IntrinsicFunctions for Release', 'ok')
        else:
            send('No IntrinsicFunctions for Release', '')

    def set_runtime_type_info(self):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        # RuntimeTypeInfo
        gr_debug_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeTypeInfo' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        gr_debug_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeTypeInfo' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if gr_debug_x64 is not None and gr_debug_x86 is not None:
            if 'true' in gr_debug_x64.text and gr_debug_x86.text:
                self.win_deb_flags += ' /GR'
                send('RuntimeTypeInfo for Debug', 'ok')
        else:
            send('No RuntimeTypeInfo for Debug', '')

        gr_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeTypeInfo' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        gr_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:RuntimeTypeInfo' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if gr_release_x86 is not None and gr_release_x64 is not None:
            if 'true' in gr_release_x64.text and gr_release_x86.text:
                self.win_rel_flags += ' /GR'
                send('RuntimeTypeInfo for Release', 'ok')
        else:
            send('No RuntimeTypeInfo for Release', '')

    def set_function_level_linking(self):
        """
        Set FunctionLevelLinking flag: /Gy

        """

        gy_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:FunctionLevelLinking' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        gy_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:FunctionLevelLinking' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if gy_release_x86 is not None and gy_release_x64 is not None:
            if 'true' in gy_release_x86.text and 'true' in gy_release_x64.text:
                self.win_rel_flags += ' /Gy'
                send('FunctionLevelLinking for release.', 'ok')
        else:
            send('No FunctionLevelLinking for release.', '')

    def set_generate_debug_information(self):
        """
        Set GenerateDebugInformation flag: /Zi

        """

        zi_debug_x86 = self.tree.find(
            '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        zi_debug_x64 = self.tree.find(
            '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if zi_debug_x86 is not None and zi_debug_x64 is not None:
            if 'true' in zi_debug_x86.text and zi_debug_x64.text:
                self.win_deb_flags += ' /Zi'
                send('GenerateDebugInformation for debug.', 'ok')
        else:
            send('No GenerateDebugInformation for debug.', '')

        zi_release_x86 = self.tree.find(
            '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        zi_release_x64 = self.tree.find(
            '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if zi_release_x86 is not None and zi_release_x64 is not None:
            if 'true' in zi_release_x86.text and zi_release_x64.text:
                self.win_rel_flags += ' /Zi'
                send('GenerateDebugInformation for release.', 'ok')
        else:
            send('No GenerateDebugInformation for release.', '')

    def set_exception_handling(self):
        """
        Set ExceptionHandling flag: /EHsc

        """

        ehs_debug_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:ExceptionHandling' % self.definitiongroups['debug']['x86'],
            namespaces=self.ns
        )
        ehs_debug_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:ExceptionHandling' % self.definitiongroups['debug']['x64'],
            namespaces=self.ns
        )
        if ehs_debug_x86 is not None and ehs_debug_x64 is not None:
            if 'false' in ehs_debug_x86.text and ehs_debug_x64.text:
                send('No ExceptionHandling for debug.', '')
        else:
            self.win_deb_flags += ' /EHsc'
            send('ExceptionHandling for debug.', 'ok')

        ehs_release_x86 = self.tree.find(
            '%s/ns:ClCompile/ns:ExceptionHandling' % self.definitiongroups['release']['x86'],
            namespaces=self.ns
        )
        ehs_release_x64 = self.tree.find(
            '%s/ns:ClCompile/ns:ExceptionHandling' % self.definitiongroups['release']['x64'],
            namespaces=self.ns
        )
        if ehs_release_x86 is not None and ehs_release_x64 is not None:
            if 'false' in ehs_release_x86.text and ehs_release_x64.text:
                send('No ExceptionHandling option for release.', '')
        else:
            self.win_rel_flags += ' /EHsc'
            send('ExceptionHandling for release.', 'ok')
