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

from cmake_converter.utils import take_name_from_list_case_ignore, normalize_path, message
from cmake_converter.utils import write_property_of_settings, set_unix_slash, get_configuration_type

cl_flags = 'cl_flags'
ln_flags = 'ln_flags'
defines = 'defines'
default_value = 'default_value'
pch_macro_text = """MACRO(ADD_PRECOMPILED_HEADER PrecompiledHeader PrecompiledSource SourcesVar)
    if(MSVC)
        set(PrecompiledBinary "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.pch")
        SET_SOURCE_FILES_PROPERTIES(${PrecompiledSource}
                                    PROPERTIES COMPILE_FLAGS "/Yc\\"${PrecompiledHeader}\\" """ +\
                                                            """/Fp\\"${PrecompiledBinary}\\""
                                               OBJECT_OUTPUTS "${PrecompiledBinary}")
        SET_SOURCE_FILES_PROPERTIES(${${SourcesVar}}
                                    PROPERTIES COMPILE_FLAGS "/Yu\\"${PrecompiledHeader}\\" """ +\
                                                            """/Fp\\"${PrecompiledBinary}\\""
                                               OBJECT_DEPENDS "${PrecompiledBinary}")
    endif()
    LIST(INSERT ${SourcesVar} 0 ${PrecompiledSource})
ENDMACRO(ADD_PRECOMPILED_HEADER)\n
"""


class Flags(object):
    """
        Class who manage flags of projects
    """

    def __init__(self, context):
        self.context = context
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.settings = context['settings']

    def write_defines_and_flags(self, compiler_check, cmake_file):
        """
        Get and write Preprocessor Macros definitions

        :param compiler_check: type of compiler (MSVC, ...)
        :type compiler_check: str
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        # normalize
        for setting in self.settings:
            self.settings[setting]['defines_str'] = ';'.join(self.settings[setting][defines])
            self.settings[setting]['cl_str'] = ';'.join(self.settings[setting][cl_flags])

        write_property_of_settings(
            cmake_file, self.settings, self.context['sln_configurations_map'],
            'target_compile_definitions(${PROJECT_NAME} PRIVATE', ')', 'defines_str'
        )
        cmake_file.write('\n')
        cmake_file.write('if({0})\n'.format(compiler_check))
        write_property_of_settings(
            cmake_file, self.settings, self.context['sln_configurations_map'],
            'target_compile_options(${PROJECT_NAME} PRIVATE', ')', 'cl_str', indent='    '
        )

        settings_of_arch = {}
        for sln_setting in self.context['sln_configurations_map']:
            arch = sln_setting.split('|')[1]
            if arch not in settings_of_arch:
                settings_of_arch[arch] = {}
            settings_of_arch[arch][sln_setting] = sln_setting

        first_arch = True
        for arch in settings_of_arch:
            if first_arch:
                cmake_file.write(
                    '    if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\")\n'.format(arch)
                )
            else:
                cmake_file.write(
                    '    elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\")\n'.format(arch)
                )
            first_arch = False
            for sln_setting in settings_of_arch[arch]:
                sln_conf = sln_setting.split('|')[0]
                mapped_setting_name = self.context['sln_configurations_map'][sln_setting]
                mapped_setting = self.settings[mapped_setting_name]
                if mapped_setting[ln_flags]:
                    configuration_type = get_configuration_type(mapped_setting_name, self.context)
                    if configuration_type:
                        if 'StaticLibrary' in configuration_type:
                            cmake_file.write(
                                '        set_target_properties(${{PROJECT_NAME}}'
                                ' PROPERTIES STATIC_LIBRARY_FLAGS_{0} "{1}")\n'
                                .format(sln_conf.upper(), ' '.join(mapped_setting[ln_flags]))
                            )
                        else:
                            cmake_file.write(
                                '        set_target_properties(${{PROJECT_NAME}} PROPERTIES '
                                'LINK_FLAGS_{0} "{1}")\n'
                                .format(sln_conf.upper(), ' '.join(mapped_setting[ln_flags]))
                            )
        cmake_file.write('    else()\n')
        cmake_file.write(
            '         message(WARNING "${CMAKE_VS_PLATFORM_NAME} arch is not supported!")\n')
        cmake_file.write('    endif()\n')
        cmake_file.write('endif()\n\n')

    @staticmethod
    def write_target_headers_only_artifact(cmake_file):
        """
        Add a dummy target to given CMake file

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message('CMake will show fake custom Library.', 'warn')
        cmake_file.write('add_custom_target(${PROJECT_NAME} SOURCES ${HEADERS_FILES})\n\n')


class CPPFlags(Flags):
    """
        Class who check and create compilation flags
    """

    available_std = ['c++11', 'c++14', 'c++17']

    def __init__(self, context):
        Flags.__init__(self, context)
        self.propertygroup = context['property_groups']
        self.definitiongroups = context['definition_groups']
        self.std = context['std']

    def define_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.define_windows_flags()
        self.define_defines()
        # self.define_linux_flags()
        # TODO: redo with generator expression for each setting(configuration)

    def define_linux_flags(self, cmake_file):
        """
        Define the Flags for Linux platforms

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if self.std:
            if self.std in self.available_std:
                message('Cmake will use C++ std %s.' % self.std, 'info')
                linux_flags = '-std=%s' % self.std
            else:
                message(
                    'C++ std %s version does not exist. CMake will use "c++11" instead' % self.std,
                    'warn'
                )
                linux_flags = '-std=c++11'
        else:
            message('No C++ std version specified. CMake will use "c++11" by default.', 'info')
            linux_flags = '-std=c++11'
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            for ref in references:
                reference = str(ref.get('Include'))
                if '\\' in reference:
                    reference = set_unix_slash(reference)
                lib = os.path.splitext(path.basename(reference))[0]

                if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
                    linux_flags += ' -fPIC'

        cmake_file.write('if(NOT MSVC)\n')
        cmake_file.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} %s")\n' % linux_flags)
        cmake_file.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        cmake_file.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        cmake_file.write('   endif()\n')
        cmake_file.write('endif(NOT MSVC)\n\n')

    def define_defines(self):
        """
        Defines preprocessor definitions in current settings

        """

        for setting in self.settings:
            define = self.tree.find(
                '{0}/ns:ClCompile/ns:PreprocessorDefinitions'.format(
                    self.definitiongroups[setting]),
                namespaces=self.ns
            )
            if define is not None:
                for preproc in define.text.split(";"):
                    if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                        self.settings[setting][defines].append(preproc)
                # Unicode
                character_set = self.tree.xpath(
                    '{0}/ns:CharacterSet'.format(self.propertygroup[setting]),
                    namespaces=self.ns)
                if character_set is not None:
                    if 'Unicode' in character_set[0].text:
                        self.settings[setting][defines].append('UNICODE')
                        self.settings[setting][defines].append('_UNICODE')
                    if 'MultiByte' in character_set[0].text:
                        self.settings[setting][defines].append('_MBCS')
                message('PreprocessorDefinitions for {0}'.format(setting), '')

    def do_precompiled_headers(self, files):
        """
        Add precompiled headers to settings

        :param files: project files instance
        :type files: cmake_converter.project_files.ProjectFiles
        """

        pch_header_path = ''
        pch_source_path = ''

        for setting in self.settings:
            precompiled_header_values = {
                'Use': {'PrecompiledHeader': 'Use'},
                'NotUsing': {'PrecompiledHeader': 'NotUsing'},
                'Create': {'PrecompiledHeader': 'Create'},
                default_value: {'PrecompiledHeader': 'NotUsing'}
            }
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:PrecompiledHeader'
                          .format(self.definitiongroups[setting]),
                          precompiled_header_values)

            precompiled_header_file_values = {default_value: {'PrecompiledHeaderFile': 'stdafx.h'}}
            flag_value = self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:PrecompiledHeaderFile'.format(self.definitiongroups[setting]),
                precompiled_header_file_values
            )
            if flag_value:
                self.settings[setting]['PrecompiledHeaderFile'] = [flag_value]

            if self.settings[setting]['PrecompiledHeader'][0] == 'Use' and pch_header_path == '':
                pch_header_name = self.settings[setting]['PrecompiledHeaderFile'][0]
                found = False
                founded_pch_h_path = ''
                for headers_path in files.headers:
                    for header in files.headers[headers_path]:
                        if header.lower() == pch_header_name.lower():
                            found = True
                            founded_pch_h_path = headers_path
                            pch_header_name = header
                        if found:
                            break
                    if found:
                        break

                pch_source_name = pch_header_name.replace('.h', '.cpp')
                real_pch_cpp = ''
                real_pch_cpp_path = ''
                if founded_pch_h_path in files.sources:
                    real_pch_cpp = take_name_from_list_case_ignore(
                        files.sources[founded_pch_h_path], pch_source_name
                    )
                    real_pch_cpp_path = founded_pch_h_path
                else:
                    for src_path in files.sources:
                        for src in files.sources[src_path]:
                            if pch_source_name == src:
                                real_pch_cpp = take_name_from_list_case_ignore(
                                    files.sources[src_path], src
                                )
                                real_pch_cpp_path = src_path
                if founded_pch_h_path:
                    founded_pch_h_path += '/'
                pch_header_path = founded_pch_h_path + pch_header_name
                if real_pch_cpp_path:
                    real_pch_cpp_path += '/'
                pch_source_path = real_pch_cpp_path + real_pch_cpp
            self.settings[setting]['PrecompiledHeaderFile'] = pch_header_path
            self.settings[setting]['PrecompiledSourceFile'] = pch_source_path

    def define_windows_flags(self):
        """
        Define the Flags for Win32 platforms

        """

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
        self.set_inline_function_expansion()
        self.set_intrinsic_functions()
        self.set_string_pooling()
        self.set_basic_runtime_checks()
        self.set_runtime_library()
        self.set_function_level_linking()
        self.set_warning_level()
        self.set_warning_as_errors()
        self.set_debug_information_format()
        self.set_compile_as()
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
        Return flag helper
        :param setting: related setting (Release|Win32, Debug|x64,...)
        :type setting: str
        :param xpath: xpath of wanted setting
        :type xpath: str
        :param flag_values: flag values for given setting
        :type flag_values: dict
        :return: correspongin flag text of setting
        :rtype: str
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
                if key not in self.settings[setting]:
                    self.settings[setting][key] = []
                self.settings[setting][key].append(value)
                flags_message += value

        flag_name = xpath.split(':')[-1]
        message('{0} for {1} is {2} '.format(flag_name, setting, flags_message), '')

        return flag_text

    def set_whole_program_optimization(self):
        """
        Set Whole Program Optimization flag: /GL and /LTCG

        """

        flag_values = {'true': {ln_flags: '/LTCG', cl_flags: '/GL'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:WholeProgramOptimization'.format(self.propertygroup[setting]),
                          flag_values)

    def set_link_incremental(self):
        """
        Set LinkIncremental flag: /INCREMENTAL

        """

        flag_values = {
            'true': {ln_flags: '/INCREMENTAL'},
            'false': {ln_flags: '/INCREMENTAL:NO'},
            default_value: {}
        }

        for setting in self.settings:
            conf_type = get_configuration_type(setting, self.context)
            if conf_type and 'StaticLibrary' in conf_type:
                continue
            value = self.set_flag(
                setting, '{0}/ns:LinkIncremental'.format(
                    self.propertygroup[setting].replace(' and @Label="Configuration"', '')
                ),
                flag_values
            )
            if not value:
                value = self.set_flag(
                    setting,
                    '//ns:LinkIncremental[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"]'
                    .format(setting), flag_values
                )
            if not value:
                self.settings[setting][ln_flags].append('/INCREMENTAL')  # default

    def set_force_conformance_in_for_loop_scope(self):
        """
        Set flag: ForceConformanceInForLoopScope

        """

        flag_values = {
            'true': {cl_flags: '/Zc:forScope'},
            'false': {cl_flags: '/Zc:forScope-'},
            default_value: {cl_flags: '/Zc:forScope'}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:ForceConformanceInForLoopScope'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def set_remove_unreferenced_code_data(self):
        """
        Set flag: RemoveUnreferencedCodeData

        """

        flag_values = {
            'true': {cl_flags: '/Zc:inline'},
            'false': {cl_flags: ''},
            default_value: {cl_flags: '/Zc:inline'}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:RemoveUnreferencedCodeData'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def set_use_debug_libraries(self):
        """
        Set Use Debug Libraries flag: /MD

        """
        for setting in self.settings:
            md = self.tree.xpath(
                '{0}/ns:UseDebugLibraries'.format(self.propertygroup[setting]), namespaces=self.ns
            )
            if md:
                if 'true' in md[0].text:
                    self.settings[setting]['use_debug_libs'] = True
                else:
                    self.settings[setting]['use_debug_libs'] = False
                message('UseDebugLibrairies for {0}'.format(setting), '')
            else:
                message('No UseDebugLibrairies for {0}'.format(setting), '')

    def set_warning_level(self):
        """
        Set Warning level for Windows: /W

        """
        flag_values = {
            'Level1': {cl_flags: '/W1'},
            'Level2': {cl_flags: '/W2'},
            'Level3': {cl_flags: '/W3'},
            'Level4': {cl_flags: '/W4'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:WarningLevel'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_warning_as_errors(self):
        """
        Set TreatWarningAsError: /WX

        """
        flag_values = {
            'true': {cl_flags: '/WX'},
            'false': {},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:TreatWarningAsError'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_disable_specific_warnings(self):
        """
        Set DisableSpecificWarnings: /wd*

        """
        for setting in self.settings:
            specific_warnings_node = self.tree.xpath(
                '{0}/ns:ClCompile/ns:DisableSpecificWarnings'.format(
                    self.definitiongroups[setting]), namespaces=self.ns
            )
            if specific_warnings_node:
                flags = []
                for sw in specific_warnings_node[0].text.strip().split(";"):
                    sw = sw.strip()
                    if sw != '%(DisableSpecificWarnings)':
                        flag = '/wd{0}'.format(sw)
                        flags.append(flag)
                        self.settings[setting][cl_flags].append(flag)
                message('DisableSpecificWarnings for {0} : {1}'.format(setting, ';'.join(flags)),
                        '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    def set_additional_options(self):
        """
        Set Additional options

        """
        for setting in self.settings:
            add_opt = self.tree.xpath(
                '{0}/ns:ClCompile/ns:AdditionalOptions'.format(
                    self.definitiongroups[setting]), namespaces=self.ns
            )
            if add_opt:
                for opt in add_opt[0].text.strip().split(" "):
                    opt = opt.strip()
                    if opt != '' and opt != '%(AdditionalOptions)':
                        self.settings[setting][cl_flags].append(opt)
                    message('Additional Options for {0} : {1}'.format(setting, opt), '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    def set_basic_runtime_checks(self):
        """
        Set Basic Runtime Checks flag: /RTC*

        """
        flag_values = {
            'StackFrameRuntimeCheck': {cl_flags: '/RTCs'},
            'UninitializedLocalUsageCheck': {cl_flags: '/RTCu'},
            'EnableFastChecks': {cl_flags: '/RTC1'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:BasicRuntimeChecks'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_runtime_library(self):
        """
        Set RuntimeLibrary flag: /MDd

        """

        # RuntimeLibrary
        for setting in self.settings:
            mdd_value = self.tree.find(
                '{0}/ns:ClCompile/ns:RuntimeLibrary'.format(self.definitiongroups[setting]),
                namespaces=self.ns
            )
            mdd = '/MDd'
            m_d = '/MD'
            mtd = '/MTd'
            m_t = '/MT'

            if 'use_debug_libs' in self.settings[setting]:
                if self.settings[setting]['use_debug_libs']:
                    m_d = '/MDd'
                    m_t = '/MTd'
                else:
                    mdd = '/MD'
                    mtd = '/MT'

            cl_flag_value = ''
            if mdd_value is not None:
                if 'MultiThreadedDebugDLL' == mdd_value.text:
                    cl_flag_value = mdd
                if 'MultiThreadedDLL' == mdd_value.text:
                    cl_flag_value = m_d
                if 'MultiThreaded' == mdd_value.text:
                    cl_flag_value = m_t
                if 'MultiThreadedDebug' == mdd_value.text:
                    cl_flag_value = mtd
                message('RuntimeLibrary {0} for {1}'.format(mdd_value.text, setting), '')
            else:
                cl_flag_value = m_d  # default
                message('Default RuntimeLibrary {0} for {1}'.format(m_d, setting), '')

            if cl_flag_value:
                self.settings[setting][cl_flags].append(cl_flag_value)

    def set_string_pooling(self):
        """
        Set StringPooling flag: /GF

        """
        flag_values = {
            'true': {cl_flags: '/GF'},
            'false': {cl_flags: '/GF-'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:StringPooling'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_optimization(self):
        """
        Set Optimization flag: /Od

        """
        flag_values = {
            'Disabled': {cl_flags: '/Od'},
            'MinSpace': {cl_flags: '/O1'},
            'MaxSpeed': {cl_flags: '/O2'},
            'Full': {cl_flags: '/Ox'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:Optimization'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_inline_function_expansion(self):
        """
        Set Inline Function Expansion flag: /Ob

        """
        flag_values = {
            'Disabled': {cl_flags: '/Ob0'},
            'OnlyExplicitInline': {cl_flags: '/Ob1'},
            'AnySuitable': {cl_flags: '/Ob2'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:InlineFunctionExpansion'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def set_intrinsic_functions(self):
        """
        Set Intrinsic Functions flag: /Oi

        """
        flag_values = {
            'true': {cl_flags: '/Oi'},
            'false': {},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:IntrinsicFunctions'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_runtime_type_info(self):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        flag_values = {
            'true': {cl_flags: '/GR'},
            'false': {},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:RuntimeTypeInfo'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_function_level_linking(self):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        flag_values = {
            'true': {cl_flags: '/Gy'},
            'false': {},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:FunctionLevelLinking'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_debug_information_format(self):
        """
        Set GenerateDebugInformation flag: /Zi

        """
        flag_values = {
            'ProgramDatabase': {cl_flags: '/Zi'},
            'EditAndContinue': {cl_flags: '/ZI'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:DebugInformationFormat'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_compile_as(self):
        """
        Set Compile As flag: /TP, TC

        """
        flag_values = {
            'CompileAsCpp': {cl_flags: '/TP'},
            'CompileAsC': {cl_flags: '/TC'},
            default_value: {}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:CompileAs'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_generate_debug_information(self):
        """
        Set GenerateDebugInformation flag: /DEBUG

        """
        flag_values = {
            'DebugFull': {ln_flags: '/DEBUG:FULL'},
            'DebugFastLink': {ln_flags: '/DEBUG:FASTLINK'},
            'true': {ln_flags: '/DEBUG'},
            'false': {},
            default_value: {ln_flags: '/DEBUG:FULL'}
        }

        for setting in self.settings:
            conf_type = get_configuration_type(setting, self.context)
            if conf_type and 'StaticLibrary' in conf_type:
                continue

            self.set_flag(
                setting,
                '{0}/ns:Link/ns:GenerateDebugInformation'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_floating_point_model(self):
        """
        Set FloatingPointModel flag: /fp

        """
        flag_values = {
            'Precise': {cl_flags: '/fp:precise'},
            'Strict': {cl_flags: '/fp:strict'},
            'Fast': {cl_flags: '/fp:fast'},
            default_value: {cl_flags: '/fp:precise'}
        }

        for setting in self.settings:
            self.set_flag(
                setting, '{0}/ns:ClCompile/ns:FloatingPointModel'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def set_exception_handling(self):
        """
        Set ExceptionHandling flag: /EHsc

        """
        flag_values = {
            'false': {},
            'true': {cl_flags: '/EHsc'},
            'Async': {cl_flags: '/EHa'},
            default_value: {cl_flags: '/EHsc'}
        }

        for setting in self.settings:
            self.set_flag(
                setting, '{0}/ns:ClCompile/ns:ExceptionHandling'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def set_buffer_security_check(self):
        """
        Set BufferSecurityCheck flag: /GS

        """
        flag_values = {
            'false': {},
            'true': {cl_flags: '/GS'},
            default_value: {cl_flags: '/GS'}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:BufferSecurityCheck'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_diagnostics_format(self):
        """
        Set DiagnosticsFormat flag : /GS

        """
        flag_values = {
            'Classic': {cl_flags: '/diagnostics:classic'},
            'Column': {cl_flags: '/diagnostics:column'},
            'Caret': {cl_flags: '/diagnostics:caret'},
            default_value: {cl_flags: '/diagnostics:classic'}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:DiagnosticsFormat'.format(self.definitiongroups[setting]),
                flag_values
            )

    def set_treatwchar_t_as_built_in_type(self):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        flag_values = {
            'false': {cl_flags: '/Zc:wchar_t-'},
            'true': {cl_flags: '/Zc:wchar_t'},
            default_value: {cl_flags: '/Zc:wchar_t'}
        }

        for setting in self.settings:
            self.set_flag(
                setting,
                '{0}/ns:ClCompile/ns:TreatWChar_tAsBuiltInType'.format(
                    self.definitiongroups[setting]),
                flag_values
            )

    def setting_has_pch(self, setting):
        """
        Return if there is precompiled header or not for given setting

        :param setting: related setting (Release|x64, Debug|Win32,...)
        :type setting: str
        :return: if use PCH or not
        :rtype: bool
        """

        has_pch = self.settings[setting]['PrecompiledHeader']

        return 'Use' in has_pch

    def write_precompiled_headers_macro(self, cmake_file):
        """
        Write Precompiled header macro (only for MSVC compiler)

        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        need_pch_macro = False
        for setting in self.settings:
            if self.setting_has_pch(setting):
                need_pch_macro = True
                break

        if need_pch_macro:
            cmake_file.write(pch_macro_text)

    def write_precompiled_headers(self, setting, cmake_file):
        """
        Write precompiled headers, if needed, on given CMake file

        :param setting: related setting (Release|x64, Debug|Win32,...)
        :type setting: str
        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        pch_header = self.settings[setting]['PrecompiledHeaderFile']
        pch_source = self.settings[setting]['PrecompiledSourceFile']
        working_path = os.path.dirname(self.context['vcxproj_path'])
        cmake_file.write(
            'ADD_PRECOMPILED_HEADER("{0}" "{1}" SRC_FILES)\n\n'.format(
                os.path.basename(pch_header), normalize_path(working_path, pch_source)
            )
        )

    def write_target_artifact(self, cmake_file):
        """
        Add Library or Executable target

        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """
        setting = ''
        for s in self.settings:
            setting = s

        cmake_file.write('# Warning: pch and target are the same for every configuration\n')
        if self.setting_has_pch(setting):
            self.write_precompiled_headers(setting, cmake_file)

        configuration_type = None
        for s in self.settings:
            configuration_type = get_configuration_type(s, self.context)
            if configuration_type:
                break
        if configuration_type:
            if configuration_type == 'DynamicLibrary':
                cmake_file.write('add_library(${PROJECT_NAME} SHARED')
                message('CMake will build a SHARED Library.', '')
            elif configuration_type == 'StaticLibrary':  # pragma: no cover
                cmake_file.write('add_library(${PROJECT_NAME} STATIC')
                message('CMake will build a STATIC Library.', '')
            else:  # pragma: no cover
                cmake_file.write('add_executable(${PROJECT_NAME} ')
                message('CMake will build an EXECUTABLE.', '')
            if not self.context['has_only_headers']:
                cmake_file.write(' ${SRC_FILES}')
            if self.context['has_headers']:
                cmake_file.write(' ${HEADERS_FILES}')
            cmake_file.write(')\n\n')


class FortranFlags(Flags):
    """
        Class who check and create compilation flags for Fortran compiler
    """

    def __init__(self, context):
        Flags.__init__(self, context)
        self.vcxproj_path = context['vcxproj_path']

    def set_flag(self, node, attr, flag_values):
        """
        Set flag helper

        :param node:
        :param attr:
        :param flag_values:
        :return:
        """

        for setting in self.settings:
            values = None
            if default_value in flag_values:
                values = flag_values[default_value]

            # flag_text = ''
            flag_text = self.settings[setting][node].get(attr)
            if flag_text in flag_values:
                values = flag_values[flag_text]

            flags_message = ''
            if values is not None:
                for key in values:
                    value = values[key]
                    if key not in self.settings[setting]:
                        self.settings[setting][key] = []
                    self.settings[setting][key].append(value)
                    flags_message += value

            message('{0} for {1} is {2} '.format(attr, setting, flags_message), '')

    def define_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.set_suppress_startup_banner()
        self.set_debug_information_format()
        self.set_optimization()
        self.set_preprocess_source_file()
        self.set_source_file_format()
        self.set_default_inc_and_use_path()
        self.set_fixed_form_line_length()
        self.set_open_mp()
        self.set_disable_specific_diagnostics()
        self.set_real_kind()
        self.set_local_variable_storage()
        self.set_init_local_var_to_nan()
        self.set_floating_point_exception_handling()
        self.set_extend_single_precision_constants()
        self.set_string_length_arg_passing()
        self.set_traceback()
        self.set_runtime_checks()
        self.set_runtime_library()
        self.set_disable_default_lib_search()
        self.set_additional_options()

    def set_fixed_form_line_length(self):
        """
        Set fixed form line length

        """
        flag_values = {
            'fixedLength80': {cl_flags: '-extend_source:80'},
            'fixedLength132': {cl_flags: '-extend_source:132'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'FixedFormLineLength', flag_values)

    def set_default_inc_and_use_path(self):
        """
        Set default include and path

        """

        flag_values = {
            'defaultIncludeCurrent': {cl_flags: '-assume:nosource_include'},
            default_value: {cl_flags: '-assume:source_include'}
        }
        self.set_flag('VFFortranCompilerTool', 'DefaultIncAndUsePath', flag_values)

    def set_open_mp(self):
        """
        Set open MP flag

        """
        flag_values = {
            'OpenMPParallelCode': {cl_flags: '-Qopenmp'},
            'OpenMPSequentialCode': {cl_flags: '-Qopenmp_stubs'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'OpenMP', flag_values)

    def set_disable_specific_diagnostics(self):
        """
        Set disable specific diagnostic flag

        """

        for setting in self.settings:
            # TODO: split list
            opt = self.settings[setting]['VFFortranCompilerTool'].get('DisableSpecificDiagnostics')
            if opt:
                self.settings[setting][cl_flags].append('-Qdiag-disable:{0}'.format(opt))

    def set_string_length_arg_passing(self):
        """
        Set string lengh arg parsing

        """
        flag_values = {
            'strLenArgsMixed': {cl_flags: '-iface:mixed_str_len_arg'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'StringLengthArgPassing', flag_values)

    def set_runtime_library(self):
        """
        Set runtime library flag

        """
        flag_values = {
            'rtMultiThreadedDLL': {cl_flags: '-libs:dll;-threads'},
            'rtQuickWin': {cl_flags: '-libs:qwin'},
            'rtStandardGraphics': {cl_flags: '-libs:qwins'},
            'rtMultiThreadedDebug': {cl_flags: '-libs:static;-threads;-dbglibs'},
            'rtMultiThreadedDebugDLL': {cl_flags: '-libs:dll;-threads;-dbglibs'},
            'rtQuickWinDebug': {cl_flags: '-libs:qwin;-dbglibs'},
            'rtStandardGraphicsDebug': {cl_flags: '-libs:qwins;-dbglibs'},
            default_value: {cl_flags: '-libs:static;-threads'}
        }
        self.set_flag('VFFortranCompilerTool', 'RuntimeLibrary', flag_values)

    def set_disable_default_lib_search(self):
        """
        Set disable default lib search

        """
        flag_values = {
            'true': {cl_flags: '-libdir:noauto'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'DisableDefaultLibSearch', flag_values)

    def set_runtime_checks(self):
        """
        Set runtime checks flag

        """
        flag_values = {
            'rtChecksAll': {cl_flags: '-check:all'},
            'rtChecksNone': {cl_flags: '-check:none'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'RuntimeChecks', flag_values)

    def set_traceback(self):
        """
        Set traceback flag

        """
        flag_values = {
            'true': {cl_flags: '-traceback'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'Traceback', flag_values)

    def set_extend_single_precision_constants(self):
        """
        Set extend single precision constants flag

        """
        flag_values = {
            'true': {cl_flags: '-fpconstant'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'ExtendSinglePrecisionConstants', flag_values)

    def set_floating_point_exception_handling(self):
        """
        Set floating exception handling

        """
        flag_values = {
            'fpe0': {cl_flags: '-fpe0'},
            'fpe1': {cl_flags: '-fpe1'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'FloatingPointExceptionHandling', flag_values)

    def set_init_local_var_to_nan(self):
        """
        Set init local var to NaN flag

        """
        flag_values = {
            'true': {cl_flags: '-Qtrapuv'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'InitLocalVarToNAN', flag_values)

    def set_preprocess_source_file(self):
        """
        Set preprocess source file flag

        """
        flag_values = {
            'preprocessYes': {cl_flags: '-fpp'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'Preprocess', flag_values)

    def set_optimization(self):
        """
        Set optimization flag

        """
        flag_values = {
            'optimizeMinSpace': {cl_flags: '-O1'},
            'optimizeFull': {cl_flags: '-O3'},
            'optimizeDisabled': {cl_flags: '-Od'},
            default_value: {cl_flags: '-O2'}
        }
        self.set_flag('VFFortranCompilerTool', 'Optimization', flag_values)

    def set_debug_information_format(self):
        """
        Set debug inforamtion format flag

        """
        flag_values = {
            'debugEnabled': {cl_flags: '-debug:full'},
            'debugLineInfoOnly': {cl_flags: '-debug:minimal'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'DebugInformationFormat', flag_values)

    def set_suppress_startup_banner(self):
        """
        Set supress banner flag

        """
        flag_values = {
            'true': {cl_flags: '-nologo'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'SuppressStartupBanner', flag_values)

    def set_source_file_format(self):
        """
        Set source file format flag

        """
        flag_values = {
            'fileFormatFree': {cl_flags: '-free'},
            'fileFormatFixed': {cl_flags: '-fixed'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'SourceFileFormat', flag_values)

    def set_local_variable_storage(self):
        """
        Set local variable storage flag

        """
        flag_values = {
            'localStorageAutomatic': {cl_flags: '-Qauto'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'LocalVariableStorage', flag_values)

    def set_real_kind(self):
        """
        Set real kind flag

        """
        flag_values = {
            'realKIND8': {cl_flags: '-real_size:64'},
            'realKIND16': {cl_flags: '-real_size:128'},
            default_value: {}
        }
        self.set_flag('VFFortranCompilerTool', 'RealKIND', flag_values)

    def set_additional_options(self):
        """
        Set Additional options

        """
        for setting in self.settings:
            add_opts = self.settings[setting]['VFFortranCompilerTool'].get('AdditionalOptions')
            if add_opts:
                add_opts = set_unix_slash(add_opts).split(' ')
                ready_add_opts = []
                for add_opt in add_opts:
                    add_opt = add_opt.strip()
                    if '/Qprof-dir' in add_opt:
                        name_value = add_opt.split(':')
                        add_opt = name_value[0] + ':' + normalize_path(
                            os.path.dirname(self.vcxproj_path), name_value[1]
                        )
                    add_opt = '-' + add_opt[1:]
                    ready_add_opts.append(add_opt)
                self.settings[setting][cl_flags].append(';'.join(ready_add_opts))
                message('Additional Options for {0} : {1}'.format(setting, str(add_opt)), '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    @staticmethod
    def write_target_artifact(cmake_file):
        """
        Add Library or Executable target

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message('CMake will build a STATIC Library.', '')
        cmake_file.write('add_library(${PROJECT_NAME} STATIC')
        cmake_file.write(' ${SRC_FILES}')
        cmake_file.write(')\n\n')
