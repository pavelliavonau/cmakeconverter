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

import os
import unittest2

from cmake_converter.flags import Flags, define_and_write_macro
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestFlags(unittest2.TestCase):
    """
        This file test methods of Flags class.
    """

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    vs_project = get_vcxproj_data('%s/test_files/project_test.vcxproj' % cur_dir)
    cmake_lists_test = get_cmake_lists('./')

    data_test = {
        'cmake': cmake_lists_test,
        'cmake_output': None,
        'vcxproj': vs_project,
        'dependencies': None,
        'includes': None,
        'additional_code': None,
        'std': None,
    }

    def test_init_dependencies(self):
        """Initialize Flags"""

        under_test = Flags(self.data_test)

        self.assertIsNotNone(under_test.tree)
        self.assertIsNotNone(under_test.ns)

        self.assertIsNotNone(under_test.propertygroup)
        self.assertTrue('debug' in under_test.propertygroup)
        self.assertTrue('release' in under_test.propertygroup)

        self.assertIsNotNone(under_test.definitiongroups)
        self.assertTrue('debug' in under_test.definitiongroups)
        self.assertTrue('release' in under_test.definitiongroups)

        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

    def test_write_flags(self):
        """Write Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)
        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

        under_test.write_flags()

        self.assertTrue(under_test.win_deb_flags)
        self.assertEqual(' /W4 /MD /Od /Zi /EHsc', under_test.win_deb_flags)
        self.assertTrue(under_test.win_rel_flags)
        self.assertEqual(' /W4 /GL /Od /Oi /Gy /Zi /EHsc', under_test.win_rel_flags)

        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertTrue(' /W4 /MD /Od /Zi /EHsc' in content_test)
        self.assertTrue(' /W4 /GL /Od /Oi /Gy /Zi /EHsc' in content_test)

        cmakelists_test.close()

    def test_define_linux_flags(self):
        """Define Linux Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)

        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++11 -fPIC' in content_test)

        cmakelists_test.close()

    def test_define_linux_flags_with_std(self):
        """Define Linux Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        self.data_test['std'] = 'c++17'
        under_test = Flags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++17' in content_test)
        cmakelists_test.close()

        self.data_test['cmake'] = get_cmake_lists('./')
        self.data_test['std'] = 'c++19'
        under_test = Flags(self.data_test)
        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        cmakelists_test = open('%s/CMakeLists.txt' % self.cur_dir, 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++11' in content_test)
        cmakelists_test.close()

    def test_define_windows_flags(self):
        """Define Windows Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.define_windows_flags()
        self.data_test['cmake'].close()

        self.assertTrue(under_test.win_deb_flags)
        self.assertTrue(under_test.win_rel_flags)

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertFalse('-std=c++11 -fPIC' in content_test)
        self.assertTrue(' /W4 /MD /Od /Zi /EHsc' in content_test)
        self.assertTrue(' /W4 /GL /Od /Oi /Gy /Zi /EHsc' in content_test)

        cmakelists_test.close()

    def test_define_group_properties(self):
        """Define XML Groups Properties"""

        under_test = Flags(self.data_test)

        self.assertIsNone(under_test.propertygroup['debug']['x86'])
        self.assertIsNone(under_test.propertygroup['debug']['x64'])
        self.assertIsNone(under_test.propertygroup['release']['x86'])
        self.assertIsNone(under_test.propertygroup['release']['x64'])

        self.assertIsNone(under_test.definitiongroups['debug']['x86'])
        self.assertIsNone(under_test.definitiongroups['debug']['x64'])
        self.assertIsNone(under_test.definitiongroups['release']['x86'])
        self.assertIsNone(under_test.definitiongroups['release']['x64'])

        under_test.define_group_properties()

        self.assertIsNotNone(under_test.propertygroup['debug']['x86'])
        self.assertIsNotNone(under_test.propertygroup['debug']['x64'])
        self.assertIsNotNone(under_test.propertygroup['release']['x86'])
        self.assertIsNotNone(under_test.propertygroup['release']['x64'])

        self.assertIsNotNone(under_test.definitiongroups['debug']['x86'])
        self.assertIsNotNone(under_test.definitiongroups['debug']['x64'])
        self.assertIsNotNone(under_test.definitiongroups['release']['x86'])
        self.assertIsNotNone(under_test.definitiongroups['release']['x64'])

        property_test = \
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"' \
            ' and @Label="Configuration"]'
        self.assertEqual(property_test, under_test.propertygroup['debug']['x86'])

        definition_test = \
            '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
            '$(Platform)\'==\'Debug|Win32\'"]'
        self.assertEqual(definition_test, under_test.definitiongroups['debug']['x86'])

    def test_set_warning_level(self):
        """Set Warning Level Flag"""

        under_test = Flags(self.data_test)

        under_test.set_warning_level()

        self.assertTrue('/W4' in under_test.win_deb_flags)
        self.assertTrue('/W4' in under_test.win_rel_flags)

    def test_set_whole_program_optimization(self):
        """Set Whole Program Optimization Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_whole_program_optimization()

        self.assertFalse('/GL' in under_test.win_deb_flags)
        self.assertTrue('/GL' in under_test.win_rel_flags)

    def test_set_use_debug_libraries(self):
        """Set Use Debug Libraries Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_use_debug_libraries()

        self.assertTrue('/MD' in under_test.win_deb_flags)
        self.assertFalse('/MD' in under_test.win_rel_flags)

    def test_set_runtime_library(self):
        """Set Runtime Library Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_runtime_library()

        self.assertFalse('/MDd' in under_test.win_deb_flags)
        self.assertFalse('/MDd' in under_test.win_rel_flags)

    def test_set_optimization(self):
        """Set Optimization Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_optimization()

        self.assertTrue('/Od' in under_test.win_deb_flags)
        self.assertTrue('/Od' in under_test.win_rel_flags)

    def test_set_intrinsic_functions(self):
        """Set Intrinsic Functions Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_intrinsic_functions()

        self.assertFalse('/Oi' in under_test.win_deb_flags)
        self.assertTrue('/Oi' in under_test.win_rel_flags)

    def test_set_runtime_type_info(self):
        """Set runtime Type Info Flag"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_runtime_type_info()

        self.assertFalse('/GR' in under_test.win_deb_flags)
        self.assertFalse('/GR' in under_test.win_rel_flags)

    def test_set_function_level_linking(self):
        """Set Function Level Linking"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_function_level_linking()

        self.assertTrue('/Gy' in under_test.win_rel_flags)

    def test_set_generate_debug_information(self):
        """Set Generate Debug Information"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_generate_debug_information()

        self.assertTrue('/Zi' in under_test.win_deb_flags)
        self.assertTrue('/Zi' in under_test.win_rel_flags)

    def test_set_exception_handling(self):
        """Set Exception Handling"""

        under_test = Flags(self.data_test)

        under_test.define_group_properties()
        under_test.set_exception_handling()

        self.assertTrue('/EHsc' in under_test.win_deb_flags)
        self.assertTrue('/EHsc' in under_test.win_rel_flags)

    def test_define_and_write_macro(self):
        """Define and Write Macros"""

        self.data_test['cmake'] = get_cmake_lists('./')
        define_and_write_macro(self.data_test)

        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt', 'r')
        under_test = cmakelists_test.read()

        macros_test = [
            '-D_CRT_NONSTDC_NO_DEPRECATE', '-D_DEBUG', '-D_WINDOWS', '-D_USRDLL',
            '-DCORE_EXPORTS', '-DUNICODE', '-D_UNICODE'
        ]

        for macro in macros_test:
            self.assertTrue(macro in under_test)

        cmakelists_test.close()
