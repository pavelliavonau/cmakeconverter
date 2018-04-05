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
ln_flags = 'ln_flags'
defines = 'defines'
default_value = 'default_value'


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
        self.define_settings()

    def define_settings(self):
        """
        Define the settings of vcxproj

        """

        configuration_nodes = self.tree.xpath('//ns:ProjectConfiguration', namespaces=self.ns)
        if configuration_nodes:
            for configuration_node in configuration_nodes:
                configuration_data = str(configuration_node.get('Include'))
                self.settings[configuration_data] = {defines: '', cl_flags: '', ln_flags: ''}

        self.define_group_properties()

    @staticmethod
    def get_setting_name(setting):
        return setting.split('|')[0]

    def get_cmake_configuration_types(self):
        configuration_types = []
        for setting in self.settings:
            configuration_types.append(self.get_setting_name(setting))
        return configuration_types

    def get_configuration_type(self, setting):
        configurationtype = self.tree.xpath(
            '{0}/ns:ConfigurationType'.format(self.propertygroup[setting]),
            namespaces=self.ns)
        return configurationtype[0].text

    def define_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.define_windows_flags()
        self.define_defines()
        # self.define_linux_flags() # TODO: redo with generator expression for each setting(configuration)

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
                        self.settings[setting][defines] += '-D%s;' % preproc
                # Unicode
                characterSet = self.tree.xpath(
                    '{0}/ns:CharacterSet'.format(self.propertygroup[setting]),
                    namespaces=self.ns)
                if characterSet is not None:
                    if 'Unicode' in characterSet[0].text:
                        self.settings[setting][defines] += '-DUNICODE;'
                        self.settings[setting][defines] += '-D_UNICODE;'
                    if 'MultiByte' in characterSet[0].text:
                        self.settings[setting][defines] += '-D_MBCS;'
                send('PreprocessorDefinitions for {0}'.format(setting), 'ok')

    def do_precompiled_headers(self, files):
        project_has_pch = False
        for setting in self.settings:
            PrecompiledHeader_values = {'Use': {'PrecompiledHeader': 'Use'},
                                        'NotUsing': {'PrecompiledHeader': 'NotUsing'},
                                        'Create': {'PrecompiledHeader': 'Create'},
                                        default_value: {'PrecompiledHeader': 'NotUsing'}}
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:PrecompiledHeader'
                          .format(self.definitiongroups[setting]),
                          PrecompiledHeader_values)

            PrecompiledHeaderFile_values = {default_value: {'PrecompiledHeaderFile': 'stdafx.h'}}
            flag_value = self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:PrecompiledHeaderFile'
                          .format(self.definitiongroups[setting]),
                          PrecompiledHeaderFile_values)
            if flag_value != '':
                self.settings[setting]['PrecompiledHeaderFile'] = flag_value

            if not project_has_pch and self.settings[setting]['PrecompiledHeader'] == 'Use':
                for folder in files.sources:
                    pch_cpp = self.settings[setting]['PrecompiledHeaderFile'].replace('.h', '.cpp')
                    files.sources[folder].remove(pch_cpp)
                project_has_pch = True

    def define_windows_flags(self):
        """
        Define the Flags for Win32 platforms

        """

        # Define FLAGS for Windows

        # from propertygroup
        #   compilation
        self.set_use_debug_libraries()
        self.set_whole_program_optimization()
        #   linking
        self.set_generate_debug_information()
        self.set_link_incremental()

        # from definitiongroups
        #   compilation
        self.set_optimization()
        self.set_intrinsic_functions()
        self.set_string_pooling()
        self.set_runtime_library()
        self.set_function_level_linking()
        self.set_warning_level()
        self.set_warning_as_errors()
        self.set_debug_information_format()
        self.set_floating_point_model()
        self.set_runtime_type_info()
        self.set_disable_specific_warnings()
        self.set_additional_options()
        self.set_exception_handling()
        self.set_buffer_security_check()
        self.set_diagnostics_format()
        self.set_treatwchar_t_as_built_in_type()
        self.set_force_conformance_in_for_loop_scope()
        self.set_remove_unreferenced_code_data()

    def set_flag(self, setting, xpath, flag_values):
        """
        Set flag helper
        """
        flag_element = self.tree.xpath(xpath, namespaces=self.ns)

        values = None
        if default_value in flag_values:
            values = flag_values[default_value]

        flag_text = ''
        if flag_element:
            flag_text = flag_element[0].text
            if flag_text in flag_values:
                values = flag_values[flag_text]

        flags_message = ''
        if values is not None:
            for key in values:
                value = values[key]
                if not key in self.settings[setting]:
                    self.settings[setting][key] = ''
                self.settings[setting][key] += value
                flags_message += value

        flag_name = xpath.split(':')[-1]
        send('{0} for {1} is {2} '.format(flag_name, setting, flags_message), '')
        return flag_text

    def set_whole_program_optimization(self):
        """
        Set Whole Program Optimization flag: /GL and /LTCG

        """

        flag_values = {'true' : {ln_flags: ' /LTCG', cl_flags: ' /GL'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:WholeProgramOptimization'.format(self.propertygroup[setting]),
                          flag_values)

    def set_link_incremental(self):
        """
        Set LinkIncremental flag: /INCREMENTAL

        """

        flag_values = {'true' : {ln_flags: ' /INCREMENTAL'},
                       'false': {ln_flags: ' /INCREMENTAL:NO'},
                       default_value: {cl_flags: '', ln_flags: ''}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:LinkIncremental'
                        .format(self.propertygroup[setting].replace(' and @Label="Configuration"','')),
                      flag_values)

    def set_force_conformance_in_for_loop_scope(self):
        """
        Set flag: ForceConformanceInForLoopScope

        """

        flag_values = {'true' : {cl_flags: ' /Zc:forScope'},
                       'false': {cl_flags: ' /Zc:forScope-'},
                       default_value: {cl_flags: ' /Zc:forScope'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:ForceConformanceInForLoopScope'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_remove_unreferenced_code_data(self):
        """
        Set flag: RemoveUnreferencedCodeData

        """

        flag_values = {'true' : {cl_flags: ' /Zc:inline'},
                       'false': {cl_flags: ''},
                       default_value: {cl_flags: ' /Zc:inline'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:RemoveUnreferencedCodeData'
                          .format(self.definitiongroups[setting]),
                          flag_values)

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
                    self.settings[setting]['use_debug_libs'] = True
                else:
                    self.settings[setting]['use_debug_libs'] = False
                send('UseDebugLibrairies for {0}'.format(setting), 'ok')
            else:
                send('No UseDebugLibrairies for {0}'.format(setting), '')

    def set_warning_level(self):
        """
        Set Warning level for Windows: /W

        """
        for setting in self.settings:
            warning = self.tree.xpath('{0}/ns:ClCompile/ns:WarningLevel'.format(self.definitiongroups[setting])
                                      , namespaces=self.ns)
            if warning[0].text != '':
                lvl = ' /W' + warning[0].text[-1:]
                self.settings[setting][cl_flags] += lvl
                send('Warning for {0} : {1}'.format(setting, lvl), 'ok')
            else:  # pragma: no cover
                send('No Warning level.', '')

    def set_warning_as_errors(self):
        """
        Set TreatWarningAsError /WX

        """
        for setting in self.settings:
            wx = self.tree.xpath('{0}/ns:ClCompile/ns:TreatWarningAsError'.format(self.definitiongroups[setting])
                                     ,namespaces=self.ns)
            if wx:
                if 'true' in wx[0].text:
                    self.settings[setting][cl_flags] += ' /WX'
                send('TreatWarningAsError for {0} : {1}'.format(setting, wx[0].text), 'ok')
            else:
                send('No TreatWarningAsError for {0}'.format(setting), '')

    def set_disable_specific_warnings(self):
        """
        Set DisableSpecificWarnings

        """
        for setting in self.settings:
            specwarn = self.tree.xpath('{0}/ns:ClCompile/ns:DisableSpecificWarnings'
                                       .format(self.definitiongroups[setting])
                                       ,namespaces=self.ns)
            if specwarn:
                for sw in specwarn[0].text.strip().split(";"):
                    if sw != '%(DisableSpecificWarnings)':
                        self.settings[setting][cl_flags] += ' /wd{0}'.format(sw)
                send('DisableSpecificWarnings for {0} : {1}'.format(setting, specwarn[0].text.strip()), 'ok')
            else:
                send('No Additional Options for {0}'.format(setting), '')

    def set_additional_options(self):
        """
        Set Additional options

        """
        for setting in self.settings:
            addOpt = self.tree.xpath('{0}/ns:ClCompile/ns:AdditionalOptions'
                                     .format(self.definitiongroups[setting])
                                     ,namespaces=self.ns)
            if addOpt:
                for opt in addOpt[0].text.strip().split(" "):
                    if opt != '%(AdditionalOptions)':
                        self.settings[setting][cl_flags] += ' {0}'.format(opt)
                send('Additional Options for {0} : {1}'.format(setting, opt), 'ok')
            else:
                send('No Additional Options for {0}'.format(setting), '')

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

            MDd = ' /MDd'
            MD  = ' /MD'
            MTd = ' /MTd'
            MT  = ' /MT'

            if 'use_debug_libs' in self.settings[setting]:
                if self.settings[setting]['use_debug_libs']:
                    MD = ' /MDd'
                    MT  = ' /MTd'
                else:
                    MDd = ' /MD'
                    MTd  = ' /MT'

            if mdd is not None:
                if 'MultiThreadedDebugDLL' == mdd.text:
                    self.settings[setting][cl_flags] += MDd
                    send('RuntimeLibrary for {0}'.format(setting), 'ok')
                    continue

                if 'MultiThreadedDLL' == mdd.text:
                    self.settings[setting][cl_flags] += MD
                    send('RuntimeLibrary for {0}'.format(setting), 'ok')
                    continue

                if 'MultiThreaded' == mdd.text:
                    self.settings[setting][cl_flags] += MT
                    send('RuntimeLibrary for {0}'.format(setting), 'ok')
                    continue

                if 'MultiThreadedDebug' == mdd.text:
                    self.settings[setting][cl_flags] += MTd
                    send('RuntimeLibrary for {0}'.format(setting), 'ok')
                    continue
            else:
                if 'use_debug_libs' in self.settings[setting]:
                    if self.settings[setting]['use_debug_libs']:
                        self.settings[setting][cl_flags] += MTd if 'static' in setting else MDd
                        send('RuntimeLibrary for {0}'.format(setting), 'ok')
                    else:
                        self.settings[setting][cl_flags] += MT if 'static' in setting else MD
                        send('RuntimeLibrary for {0}'.format(setting), 'ok')
                else:
                    send('No RuntimeLibrary for {0}'.format(setting), '')

    def set_string_pooling(self):
        """
        Set StringPooling flag: /GF

        """

        for setting in self.settings:
            sp = self.tree.find(
                '%s/ns:ClCompile/ns:StringPooling' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if sp is not None:
                if 'true' in sp.text:
                    self.settings[setting][cl_flags] += ' /GF'
                if 'false' in sp.text:
                    self.settings[setting][cl_flags] += ' /GF-'
                send('StringPooling for {0}'.format(setting), 'ok')
            else:
                send('No StringPooling for {0}'.format(setting), '')

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
                if 'MinSpace' in opt.text:
                    self.settings[setting][cl_flags] += ' /O1'
                    send('Optimization for {0}'.format(setting), 'ok')
                if 'MaxSpeed' in opt.text:
                    self.settings[setting][cl_flags] += ' /O2'
                    send('Optimization for {0}'.format(setting), 'ok')
                if 'Full' in opt.text:
                    self.settings[setting][cl_flags] += ' /Ox'
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

    def set_debug_information_format(self):
        """
        Set GenerateDebugInformation flag: /Zi

        """

        for setting in self.settings:
            zi = self.tree.find(
                '%s/ns:ClCompile/ns:DebugInformationFormat' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if zi is not None:
                if 'ProgramDatabase' in zi.text:
                    self.settings[setting][cl_flags] += ' /Zi'
                    send('GenerateDebugInformation for {0} is {1}'.format(setting, ' /Zi'), 'ok')
                if 'EditAndContinue' in zi.text:
                    self.settings[setting][cl_flags] += ' /ZI'
                    send('GenerateDebugInformation for {0} is {1}'.format(setting, ' /ZI'), 'ok')
            else:
                send('No GenerateDebugInformation for {0}'.format(setting), '')

    def set_generate_debug_information(self):
        """
        Set GenerateDebugInformation flag: /DEBUG

        """

        for setting in self.settings:
            deb = self.tree.find(
                '%s/ns:Link/ns:GenerateDebugInformation' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if deb is not None:
                if 'true' in deb.text:
                    conf_type = self.get_configuration_type(setting)
                    if 'StaticLibrary' in conf_type:
                        continue
                    self.settings[setting][ln_flags] += ' /DEBUG'
                    send('GenerateDebugInformation for {0}'.format(setting), 'ok')
            else:
                send('No GenerateDebugInformation for {0}'.format(setting), '')

    def set_floating_point_model(self):
        """
        Set FloatingPointModel flag: /fp

        """

        for setting in self.settings:
            fp = self.tree.find(
                '%s/ns:ClCompile/ns:FloatingPointModel' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if fp is not None:
                if 'Precise' in fp.text:
                    self.settings[setting][cl_flags] += ' /fp:precise'
                if 'Strict' in fp.text:
                    self.settings[setting][cl_flags] += ' /fp:strict'
                if 'Fast' in fp.text:
                    self.settings[setting][cl_flags] += ' /fp:fast'
                send('FloatingPointModel for {0} is {1}'.format(setting, fp.text), '')
            else:
                self.settings[setting][cl_flags] += ' /fp:precise'
                send('FloatingPointModel for {0} is {1}'.format(setting, '/fp:precise'), 'ok')

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

    def set_buffer_security_check(self):
        """
        Set BufferSecurityCheck flag: /GS

        """

        for setting in self.settings:
            gs = self.tree.find(
                '%s/ns:ClCompile/ns:BufferSecurityCheck' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if gs is not None:
                if 'false' in gs.text:
                    send('No BufferSecurityCheck for {0}'.format(setting), '')
            else:
                self.settings[setting][cl_flags] += ' /GS'
                send('BufferSecurityCheck for {0}'.format(setting), 'ok')

    def set_diagnostics_format(self):
        """
        Set DiagnosticsFormat flag : /GS
        
        """

        for setting in self.settings:
            gs = self.tree.find(
                '%s/ns:ClCompile/ns:DiagnosticsFormat' % self.definitiongroups[setting],
                namespaces=self.ns
            )
            if gs is not None:
                if 'Classic' in gs.text:
                    self.settings[setting][cl_flags] += ' /diagnostics:classic'
                    send('No BufferSecurityCheck for {0}'.format(setting), '')
                if 'Column' in gs.text:
                    self.settings[setting][cl_flags] += ' /diagnostics:column'
                    send('No BufferSecurityCheck for {0}'.format(setting), '')
                if 'Caret' in gs.text:
                    self.settings[setting][cl_flags] += ' /diagnostics:caret'
                    send('No BufferSecurityCheck for {0}'.format(setting), '')
            else:
                self.settings[setting][cl_flags] += ' /diagnostics:classic'
                send('BufferSecurityCheck for {0}'.format(setting), 'ok')

    def set_treatwchar_t_as_built_in_type(self):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        for setting in self.settings:
            ch = self.tree.xpath('{0}/ns:ClCompile/ns:TreatWChar_tAsBuiltInType'
                                 .format(self.definitiongroups[setting])
                                     ,namespaces=self.ns)
            if ch:
                if 'false' in ch[0].text:
                    self.settings[setting][cl_flags] += ' /Zc:wchar_t-'
                    send('TreatWChar_tAsBuiltInType for {0} : {1}'.format(setting, ch), 'ok')
                if 'true' in ch[0].text:
                    self.settings[setting][cl_flags] += ' /Zc:wchar_t'
                    send('TreatWChar_tAsBuiltInType for {0} : {1}'.format(setting, ch), 'ok')
            else:
                self.settings[setting][cl_flags] += ' /Zc:wchar_t'
                send('TreatWChar_tAsBuiltInType for {0}: {1}'.format(setting, ch), '')
    
    def setting_has_pch(self, setting):
        """
        """
        has_pch = self.settings[setting]['PrecompiledHeader']
        return has_pch == 'Use'

    def write_precompiled_headers_macro(self):
        """
        """
        need_pch_macro = False
        for setting in self.settings:
            if self.setting_has_pch(setting):
                need_pch_macro = True
                break

        if need_pch_macro:
            cmake = self.cmake
            cmake.write('\nMACRO(ADD_PRECOMPILED_HEADER PrecompiledHeader PrecompiledSource SourcesVar)')
            cmake.write('\n    if(MSVC)')
            cmake.write('\n        set(PrecompiledBinary "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.pch")')
            cmake.write('\n        SET_SOURCE_FILES_PROPERTIES(${PrecompiledSource}')
            cmake.write('\n                                    PROPERTIES COMPILE_FLAGS "/Yc\\"${PrecompiledHeader}\\"'
                        ' /Fp\\"${PrecompiledBinary}\\""')
            cmake.write('\n                                               OBJECT_OUTPUTS "${PrecompiledBinary}")')
            cmake.write('\n        SET_SOURCE_FILES_PROPERTIES(${${SourcesVar}}')
            cmake.write('\n                                    PROPERTIES COMPILE_FLAGS "/Yu\\"${PrecompiledHeader}\\"'
                        ' /FI\\"${PrecompiledHeader}\\" /Fp\\"${PrecompiledBinary}\\""')
            cmake.write('\n                                               OBJECT_DEPENDS "${PrecompiledBinary}")')
            cmake.write('\n    endif()')
            cmake.write('\n    LIST(INSERT ${SourcesVar} 0 ${PrecompiledSource})')
            cmake.write('\nENDMACRO(ADD_PRECOMPILED_HEADER)\n')

    def write_precompiled_headers(self, setting):
        """
        """
        if not self.setting_has_pch(setting):
            return

        pch = self.settings[setting]['PrecompiledHeaderFile']
        self.cmake.write('\nADD_PRECOMPILED_HEADER("{0}" "{1}" SRC_FILES)\n'
                    .format(pch, pch.replace('.h', '.cpp')))

    def write_target_artefact(self):
        """
        Add Library or Executable target

        """
        setting = ''
        for s in self.settings:
            conf = self.get_setting_name(s).upper()
            setting = s
 
        self.cmake.write('\n# Warning: pch and target are the same for every configuration')
        self.write_precompiled_headers(setting)
        configurationtype = self.get_configuration_type(setting)
        if configurationtype == 'DynamicLibrary':
            self.cmake.write('\nadd_library(${PROJECT_NAME} SHARED')
            send('CMake will build a SHARED Library.', '')
        elif configurationtype == 'StaticLibrary':  # pragma: no cover
            self.cmake.write('\nadd_library(${PROJECT_NAME} STATIC')
            send('CMake will build a STATIC Library.', '')
        else:  # pragma: no cover
            self.cmake.write('\nadd_executable(${PROJECT_NAME} ')
            send('CMake will build an EXECUTABLE.', '')
        self.cmake.write(' ${SRC_FILES} ${HEADERS_FILES}')
        self.cmake.write(')\n')

    def write_defines_and_flags(self):
        """
        Get and write Preprocessor Macros definitions

        """
        cmake = self.cmake

        
        # self.cmake.write(
        #     '################# Flags ################\n'
        #     '# Defines Flags for Windows and Linux. #\n'
        #     '########################################\n\n'
        # )

        cmake.write('\n# Configuration settings of target\n')
        cmake.write('target_compile_definitions(${PROJECT_NAME} PRIVATE')
        for setting in self.settings:
            conf = self.get_setting_name(setting).upper()
            cmake.write(
                '\n$<$<CONFIG:{0}>: {1}>'.format(conf, self.settings[setting][defines].strip().replace('\n',';'))
            )

        cmake.write('\n)\nif(MSVC)')
        cmake.write('\n    target_compile_options(${PROJECT_NAME} PRIVATE')
        for setting in self.settings:
            conf = self.get_setting_name(setting).upper()
            cmake.write('\n    $<$<CONFIG:{0}>: {1}>'
                .format(conf, self.settings[setting][cl_flags].strip().replace(' ', ';'))
            )
        cmake.write('\n    )')
        for setting in self.settings:
            conf = self.get_setting_name(setting).upper()
            if len(self.settings[setting][ln_flags]) != 0:
                configuration_type = self.get_configuration_type(setting)
                if 'StaticLibrary' in configuration_type:
                    cmake.write(
                        '\n    set_target_properties(${{PROJECT_NAME}} PROPERTIES STATIC_LIBRARY_FLAGS_{0} "{1}")'
                        .format(conf, self.settings[setting][ln_flags])
                    )
                else:
                    cmake.write(
                        '\n    set_target_properties(${{PROJECT_NAME}} PROPERTIES LINK_FLAGS_{0} "{1}")'
                        .format(conf, self.settings[setting][ln_flags])
                    )
        cmake.write('\nendif()\n')
