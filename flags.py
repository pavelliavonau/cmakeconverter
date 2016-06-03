# -*- coding: utf-8 -*-

import os
import ntpath as path
import message as msg

class Flags(object):

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.win_deb_flags = ''
        self.win_rel_flags = ''

    def write_flags(self):
        self.cmake.write('# Flags\n')
        self.define_win_flags()
        self.define_lin_flags()

    def define_lin_flags(self):
        # Define FLAGS for Linux compiler
        linux_flags = '-std=c++11'
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            for ref in references:
                reference = str(ref.get('Include'))
                lib = os.path.splitext(path.basename(reference))[0]
                if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
                    linux_flags += ' -fPIC'

        self.cmake.write('if(NOT MSVC)\n')
        self.cmake.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ' + linux_flags + '")\n')
        self.cmake.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        self.cmake.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        self.cmake.write('   endif()\n')
        self.cmake.write('endif(NOT MSVC)\n')

    def define_win_flags(self):
        # Warning
        warning = self.tree.xpath('//ns:WarningLevel', namespaces=self.ns)[0]
        if warning.text != '':
            lvl = ' /W' + warning.text[-1:]
            self.win_deb_flags += lvl
            self.win_rel_flags += lvl
            msg.send('Warning : ' + warning.text, 'ok')
        else:
            msg.send('No Warning level.', '')

        """ PropertyGroup """
        prop_deb_x86 = '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]'
        prop_deb_x64 = '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]'
        prop_rel_x86 = '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]'
        prop_rel_x64 = '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]'

        # WholeProgramOptimization
        gl_debug_x86 = self.tree.find(prop_deb_x86 + '/ns:WholeProgramOptimization', namespaces=self.ns)
        gl_debug_x64 = self.tree.find(prop_deb_x64 + '/ns:WholeProgramOptimization', namespaces=self.ns)
        if gl_debug_x86 is not None and gl_debug_x64 is not None:
            if 'true' in gl_debug_x86.text and 'true' in gl_debug_x64.text:
                self.win_deb_flags += ' /GL'
                msg.send('WholeProgramOptimization for Debug', 'ok')
        else:
            msg.send('No WholeProgramOptimization for Debug', '')

        gl_release_x86 = self.tree.find(prop_rel_x86 + '/ns:WholeProgramOptimization', namespaces=self.ns)
        gl_release_x64 = self.tree.find(prop_rel_x64 + '/ns:WholeProgramOptimization', namespaces=self.ns)
        if gl_release_x86 is not None and gl_release_x64 is not None:
            if 'true' in gl_release_x86.text and 'true' in gl_release_x64.text:
                self.win_rel_flags += ' /GL'
                msg.send('WholeProgramOptimization for Release', 'ok')
        else:
            msg.send('No WholeProgramOptimization for Release', '')

        # UseDebugLibraries
        md_debug_x86 = self.tree.find(prop_deb_x86 + '/ns:UseDebugLibraries', namespaces=self.ns)
        md_debug_x64 = self.tree.find(prop_deb_x64 + '/ns:UseDebugLibraries', namespaces=self.ns)
        if md_debug_x64 is not None and md_debug_x86 is not None:
            if 'true' in md_debug_x86.text and 'true' in md_debug_x64.text:
                self.win_deb_flags += ' /MD'
                msg.send('UseDebugLibrairies for Debug', 'ok')
        else:
            msg.send('No UseDebugLibrairies for Debug', '')

        md_release_x86 = self.tree.find(prop_rel_x86 + '/ns:UseDebugLibraries', namespaces=self.ns)
        md_release_x64 = self.tree.find(prop_rel_x64 + '/ns:UseDebugLibraries', namespaces=self.ns)
        if md_release_x86 is not None and md_release_x64 is not None:
            if 'true' in md_release_x86.text and 'true' in md_release_x64.text:
                self.win_rel_flags += ' /MD'
                msg.send('UseDebugLibrairies for Release', 'ok')
        else:
            msg.send('No UseDebugLibrairies for Release', '')

        """ ItemDefinitionGroup """
        item_deb_x86 = '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]'
        item_deb_x64 = '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]'
        item_rel_x86 = '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]'
        item_rel_x64 = '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]'

        # RuntimeLibrary
        mdd_debug_x86 = self.tree.find(item_deb_x86 + '/ns:ClCompile/ns:RuntimeLibrary', namespaces=self.ns)
        mdd_debug_x64 = self.tree.find(item_deb_x64 + '/ns:ClCompile/ns:RuntimeLibrary', namespaces=self.ns)
        if mdd_debug_x64 is not None and mdd_debug_x86 is not None:
            if 'MultiThreadedDebugDLL' in mdd_debug_x86.text and 'MultiThreadedDebugDLL' in mdd_debug_x64.text:
                self.win_deb_flags += ' /MDd'
                msg.send('RuntimeLibrary for Debug', 'ok')
        else:
            msg.send('No RuntimeLibrary for Debug', '')

        mdd_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:RuntimeLibrary', namespaces=self.ns)
        mdd_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:RuntimeLibrary', namespaces=self.ns)
        if mdd_release_x86 is not None and mdd_release_x64 is not None:
            if 'MultiThreadedDebugDLL' in mdd_release_x86.text and 'MultiThreadedDebugDLL' in mdd_release_x64.text:
                self.win_rel_flags += ' /MDd'
                msg.send('RuntimeLibrary for Release', 'ok')
        else:
            msg.send('No RuntimeLibrary for Release', '')

        # Optimization
        opt_debug_x86 = self.tree.find(item_deb_x86 + '/ns:ClCompile/ns:Optimization', namespaces=self.ns)
        opt_debug_x64 = self.tree.find(item_deb_x64 + '/ns:ClCompile/ns:Optimization', namespaces=self.ns)
        if opt_debug_x86 is not None and opt_debug_x64 is not None:
            if 'Disabled' in opt_debug_x64.text and 'Disabled' in opt_debug_x86.text:
                self.win_deb_flags += ' /O2'
                msg.send('Optimization for Debug', 'ok')
        else:
            msg.send('No Optimization for Debug', '')

        opt_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:Optimization', namespaces=self.ns)
        opt_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:Optimization', namespaces=self.ns)
        if opt_release_x86 is not None and opt_release_x64 is not None:
            if 'MaxSpeed' in opt_release_x64.text and 'MaxSpeed' in opt_release_x86.text:
                self.win_rel_flags += ' /O2'
                msg.send('Optimization for Release', 'ok')
        else:
            msg.send('No Optimization for Release', '')

        # IntrinsicFunctions
        oi_debug_x86 = self.tree.find(item_deb_x86 + '/ns:ClCompile/ns:IntrinsicFunctions', namespaces=self.ns)
        oi_debug_x64 = self.tree.find(item_deb_x64 + '/ns:ClCompile/ns:IntrinsicFunctions', namespaces=self.ns)
        if oi_debug_x86 is not None and oi_debug_x64 is not None:
            if 'true' in oi_debug_x86.text and 'true' in oi_debug_x64.text:
                self.win_deb_flags += ' /Oi'
                msg.send('IntrinsicFunctions for Debug', 'ok')
        else:
            msg.send('No IntrinsicFunctions for Debug', '')

        oi_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:IntrinsicFunctions', namespaces=self.ns)
        oi_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:IntrinsicFunctions', namespaces=self.ns)
        if oi_release_x86 is not None and oi_release_x64 is not None:
            if 'true' in oi_release_x86.text and 'true' in oi_release_x64.text:
                self.win_rel_flags += ' /Oi'
                msg.send('IntrinsicFunctions for Release', 'ok')
        else:
            msg.send('No IntrinsicFunctions for Release', '')

        # RuntimeTypeInfo
        gr_debug_x86 = self.tree.find(item_deb_x86 + '/ns:ClCompile/ns:RuntimeTypeInfo', namespaces=self.ns)
        gr_debug_x64 = self.tree.find(item_deb_x64 + '/ns:ClCompile/ns:RuntimeTypeInfo', namespaces=self.ns)
        if gr_debug_x64 is not None and gr_debug_x86 is not None:
            if 'true' in gr_debug_x64.text and gr_debug_x86.text:
                self.win_deb_flags += ' /GR'
                msg.send('RuntimeTypeInfo for Debug', 'ok')
        else:
            msg.send('No RuntimeTypeInfo for Debug', '')

        gr_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:RuntimeTypeInfo', namespaces=self.ns)
        gr_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:RuntimeTypeInfo', namespaces=self.ns)
        if gr_release_x86 is not None and gr_release_x64 is not None:
            if 'true' in gr_release_x64.text and gr_release_x86.text:
                self.win_rel_flags += ' /GR'
                msg.send('RuntimeTypeInfo for Release', 'ok')
        else:
            msg.send('No RuntimeTypeInfo for Release', '')

        # FunctionLevelLinking
        gy_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:FunctionLevelLinking', namespaces=self.ns)
        gy_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:FunctionLevelLinking', namespaces=self.ns)
        if gy_release_x86 is not None and gy_release_x64 is not None:
            if 'true' in gy_release_x86.text and 'true' in gy_release_x64.text:
                self.win_rel_flags += ' /Gy'
                msg.send('FunctionLevelLinking for release.', 'ok')
        else:
            msg.send('No FunctionLevelLinking for release.', '')

        # GenerateDebugInformation
        zi_debug_x86 = self.tree.find(item_deb_x86 + '/ns:Link/ns:GenerateDebugInformation', namespaces=self.ns)
        zi_debug_x64 = self.tree.find(item_deb_x64 + '/ns:Link/ns:GenerateDebugInformation', namespaces=self.ns)
        if zi_debug_x86 is not None and zi_debug_x64 is not None:
            if 'true' in zi_debug_x86.text and zi_debug_x64.text:
                self.win_deb_flags += ' /Zi'
                msg.send('GenerateDebugInformation for debug.', 'ok')
        else:
            msg.send('No GenerateDebugInformation for debug.', '')

        zi_release_x86 = self.tree.find(item_rel_x86 + '/ns:Link/ns:GenerateDebugInformation', namespaces=self.ns)
        zi_release_x64 = self.tree.find(item_rel_x64 + '/ns:Link/ns:GenerateDebugInformation', namespaces=self.ns)
        if zi_release_x86 is not None and zi_release_x64 is not None:
            if 'true' in zi_release_x86.text and zi_release_x64.text:
                self.win_rel_flags += ' /Zi'
                msg.send('GenerateDebugInformation for release.', 'ok')
        else:
            msg.send('No GenerateDebugInformation for release.', '')

        # ExceptionHandling
        ehs_debug_x86 = self.tree.find(item_deb_x86 + '/ns:ClCompile/ns:ExceptionHandling', namespaces=self.ns)
        ehs_debug_x64 = self.tree.find(item_deb_x64 + '/ns:ClCompile/ns:ExceptionHandling', namespaces=self.ns)
        if ehs_debug_x86 is not None and ehs_debug_x64 is not None:
            if 'false' in ehs_debug_x86.text and ehs_debug_x64.text:
                msg.send('No ExceptionHandling for debug.', '')
        else:
            self.win_deb_flags += ' /EHsc'
            msg.send('ExceptionHandling for debug.', 'ok')

        ehs_release_x86 = self.tree.find(item_rel_x86 + '/ns:ClCompile/ns:ExceptionHandling', namespaces=self.ns)
        ehs_release_x64 = self.tree.find(item_rel_x64 + '/ns:ClCompile/ns:ExceptionHandling', namespaces=self.ns)
        if ehs_release_x86 is not None and ehs_release_x64 is not None:
            if 'false' in ehs_release_x86.text and ehs_release_x64.text:
                msg.send('No ExceptionHandling option for release.', '')
        else:
            self.win_rel_flags += ' /EHsc'
            msg.send('ExceptionHandling for release.', 'ok')

        # Define FLAGS for Windows
        self.cmake.write('if(MSVC)\n')
        if self.win_deb_flags != '':
            msg.send('Debug   FLAGS found = ' + self.win_deb_flags, 'ok')
            self.cmake.write('   set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}' + self.win_deb_flags + '")\n')
        else:
            msg.send('No Debug   FLAGS found', '')
        if self.win_rel_flags != '':
            msg.send('Release FLAGS found = ' + self.win_rel_flags, 'ok')
            self.cmake.write('   set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}' + self.win_rel_flags + '")\n')
        else:
            msg.send('No Release FLAGS found', '')
        self.cmake.write('endif(MSVC)\n')