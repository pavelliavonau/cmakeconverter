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

from cmake_converter.utils import take_name_from_list_case_ignore, normalize_path, message,\
    write_comment, is_settings_has_data
from cmake_converter.utils import write_property_of_settings, set_unix_slash, get_configuration_type

cl_flags = 'cl_flags'               # MSVC compile flags (Windows only)
ln_flags = 'ln_flags'               # MSVC link flags (Windows only)
ifort_cl_win = 'ifort_cl_win'       # ifort compile flags (Windows)
ifort_cl_unix = 'ifort_cl_unix'     # ifort compile flags (Unix)
ifort_ln = 'ifort_ln'               # ifort link flags
defines = 'defines'                 # compile definitions (cross platform)
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

    @staticmethod
    def write_defines(context, cmake_file):
        for setting in context.settings:
            context.settings[setting]['defines_str'] = ';'.join(context.settings[setting][defines])

        write_comment(cmake_file, 'Compile definitions')
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            'target_compile_definitions(${PROJECT_NAME} PRIVATE', ')', 'defines_str'
        )
        cmake_file.write('\n')

    @staticmethod
    def write_compiler_and_linker_flags(context, os_check_str, compiler_check_str,
                                        compiler_flags_key, linker_flags_key, cmake_file):
        for setting in context.settings:
            context.settings[setting]['cl_str'] =\
                ';'.join(context.settings[setting][compiler_flags_key])

        and_os_str = ''
        if os_check_str:
            and_os_str = ' AND {0}'.format(os_check_str)
        cmake_file.write('if({0}{1})\n'.format(compiler_check_str, and_os_str))
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            'target_compile_options(${PROJECT_NAME} PRIVATE', ')', 'cl_str', indent='    '
        )

        settings_of_arch = {}
        for sln_setting in context.sln_configurations_map:
            arch = sln_setting.split('|')[1]
            if arch not in settings_of_arch:
                settings_of_arch[arch] = {}
            settings_of_arch[arch][sln_setting] = sln_setting

        first_arch = True
        arch_has_link_flags = False
        for arch in settings_of_arch:
            arch_has_link_flags |= is_settings_has_data(context.sln_configurations_map,
                                                        context.settings, linker_flags_key, arch)
            if not arch_has_link_flags:
                break
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
                mapped_setting_name = context.sln_configurations_map[sln_setting]
                mapped_setting = context.settings[mapped_setting_name]
                if mapped_setting[linker_flags_key]:
                    configuration_type = get_configuration_type(mapped_setting_name, context)
                    if configuration_type:
                        if 'StaticLibrary' in configuration_type:
                            cmake_file.write(
                                '        set_target_properties(${{PROJECT_NAME}}'
                                ' PROPERTIES STATIC_LIBRARY_FLAGS_{0} "{1}")\n'
                                .format(sln_conf.upper(),
                                        ' '.join(mapped_setting[linker_flags_key]))
                            )
                        else:
                            cmake_file.write(
                                '        set_target_properties(${{PROJECT_NAME}} PROPERTIES '
                                'LINK_FLAGS_{0} "{1}")\n'
                                .format(sln_conf.upper(),
                                        ' '.join(mapped_setting[linker_flags_key]))
                            )
        if arch_has_link_flags:
            cmake_file.write('    endif()\n')
        cmake_file.write('endif()\n\n')

    def write_flags(self, context, cmake_file):
        """
        Get and write Preprocessor Macros definitions

        :param context: converter Context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """
        is_msvc = False
        for setting in context.settings:
            if cl_flags in context.settings[setting]:
                if context.settings[setting][cl_flags]:
                    is_msvc = True
                    break

        is_ifort = False
        for setting in context.settings:
            if ifort_cl_win in context.settings[setting]:
                if context.settings[setting][ifort_cl_win]:
                    is_ifort = True
                    break

        write_comment(cmake_file, 'Compile and link options')
        if is_msvc:
            self.write_compiler_and_linker_flags(context, None, 'MSVC', cl_flags, ln_flags,
                                                 cmake_file)

        if is_ifort:
            self.write_compiler_and_linker_flags(context, 'WIN32',
                                                 '${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"',
                                                 ifort_cl_win, ifort_ln, cmake_file)
            self.write_compiler_and_linker_flags(context, 'UNIX',
                                                 '${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"',
                                                 ifort_cl_unix, ifort_ln, cmake_file)

    @staticmethod
    def write_target_headers_only_artifact(cmake_file):
        """
        Add a dummy target to given CMake file

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message('CMake will show fake custom Library.', 'warn')
        cmake_file.write('add_custom_target(${PROJECT_NAME} SOURCES ${HEADERS_FILES})\n\n')

    def write_precompiled_headers_macro(self, context, cmake_file):
        pass

    def write_use_pch_macro(self, context, cmake_file):
        pass


class CPPFlags(Flags):
    """
        Class who check and create compilation flags
    """

    available_std = ['c++11', 'c++14', 'c++17']

    def define_flags(self, context):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.do_precompiled_headers(context)

        for setting in context.settings:
            context.settings[setting][cl_flags] = []
            context.settings[setting][ln_flags] = []

        self.define_windows_flags(context)
        self.define_defines(context)
        # self.define_linux_flags()
        # TODO: redo with generator expression for each setting(configuration)

    def define_linux_flags(self, context, cmake_file):
        """
        Define the Flags for Linux platforms

        :param context: converter Context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if context.std:
            if context.std in self.available_std:
                message('Cmake will use C++ std {0}.'.format(context.std), 'info')
                linux_flags = '-std=%s' % context.std
            else:
                message(
                    'C++ std {0} version does not exist. CMake will use "c++11" instead'
                    .format(context.std),
                    'warn'
                )
                linux_flags = '-std=c++11'
        else:
            message('No C++ std version specified. CMake will use "c++11" by default.', 'info')
            linux_flags = '-std=c++11'
        references = context.vcxproj['tree'].xpath('//ns:ProjectReference',
                                                   namespaces=context.vcxproj['ns'])
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

    @staticmethod
    def define_defines(context):
        """
        Defines preprocessor definitions in current settings

        """

        for setting in context.settings:
            define = context.vcxproj['tree'].find(
                '{0}/ns:ClCompile/ns:PreprocessorDefinitions'.format(
                    context.definition_groups[setting]),
                namespaces=context.vcxproj['ns']
            )
            if define is not None:
                for preproc in define.text.split(";"):
                    if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                        context.settings[setting][defines].append(preproc)
                # Unicode
                character_set = context.vcxproj['tree'].xpath(
                    '{0}/ns:CharacterSet'.format(context.property_groups[setting]),
                    namespaces=context.vcxproj['ns'])
                if character_set is not None:
                    if 'Unicode' in character_set[0].text:
                        context.settings[setting][defines].append('UNICODE')
                        context.settings[setting][defines].append('_UNICODE')
                    if 'MultiByte' in character_set[0].text:
                        context.settings[setting][defines].append('_MBCS')
                message('PreprocessorDefinitions for {0} are '.format(setting), '')

    def do_precompiled_headers(self, context):
        """
        Add precompiled headers to settings

        :param context: converter Context
        :type context: Context
        """

        pch_header_path = ''
        pch_source_path = ''

        for setting in context.settings:
            precompiled_header_values = {
                'Use': {'PrecompiledHeader': 'Use'},
                'NotUsing': {'PrecompiledHeader': 'NotUsing'},
                'Create': {'PrecompiledHeader': 'Create'},
                default_value: {'PrecompiledHeader': 'NotUsing'}
            }
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:PrecompiledHeader'
                          .format(context.definition_groups[setting]),
                          precompiled_header_values)

            precompiled_header_file_values = {default_value: {'PrecompiledHeaderFile': 'stdafx.h'}}
            flag_value = self.set_flag(context, setting,
                                       '{0}/ns:ClCompile/ns:PrecompiledHeaderFile'
                                       .format(context.definition_groups[setting]),
                                       precompiled_header_file_values
                                       )
            if flag_value:
                context.settings[setting]['PrecompiledHeaderFile'] = [flag_value]

            if context.settings[setting]['PrecompiledHeader'][0] == 'Use' and pch_header_path == '':
                pch_header_name = context.settings[setting]['PrecompiledHeaderFile'][0]
                found = False
                founded_pch_h_path = ''
                for headers_path in context.headers:
                    for header in context.headers[headers_path]:
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
                if founded_pch_h_path in context.sources:
                    real_pch_cpp = take_name_from_list_case_ignore(
                        context.sources[founded_pch_h_path], pch_source_name
                    )
                    real_pch_cpp_path = founded_pch_h_path
                else:
                    for src_path in context.sources:
                        for src in context.sources[src_path]:
                            if pch_source_name == src:
                                real_pch_cpp = take_name_from_list_case_ignore(
                                    context.sources[src_path], src
                                )
                                real_pch_cpp_path = src_path
                if founded_pch_h_path:
                    founded_pch_h_path += '/'
                pch_header_path = founded_pch_h_path + pch_header_name
                if real_pch_cpp_path:
                    real_pch_cpp_path += '/'
                pch_source_path = real_pch_cpp_path + real_pch_cpp
            context.settings[setting]['PrecompiledHeaderFile'] = pch_header_path
            context.settings[setting]['PrecompiledSourceFile'] = pch_source_path

    def define_windows_flags(self, context):
        """
        Define the Flags for Win32 platforms

        """

        # from property_groups
        #   compilation
        self.set_use_debug_libraries(context)
        self.set_whole_program_optimization(context)
        #   linking
        self.set_generate_debug_information(context)
        self.set_link_incremental(context)

        # from definition_groups
        #   compilation
        self.set_optimization(context)
        self.set_inline_function_expansion(context)
        self.set_intrinsic_functions(context)
        self.set_string_pooling(context)
        self.set_basic_runtime_checks(context)
        self.set_runtime_library(context)
        self.set_function_level_linking(context)
        self.set_warning_level(context)
        self.set_warning_as_errors(context)
        self.set_debug_information_format(context)
        self.set_compile_as(context)
        self.set_floating_point_model(context)
        self.set_runtime_type_info(context)
        self.set_disable_specific_warnings(context)
        self.set_additional_options(context)
        self.set_exception_handling(context)
        self.set_buffer_security_check(context)
        self.set_diagnostics_format(context)
        self.set_disable_language_extensions(context)
        self.set_treatwchar_t_as_built_in_type(context)
        self.set_force_conformance_in_for_loop_scope(context)
        self.set_remove_unreferenced_code_data(context)

    @staticmethod
    def set_flag(context, setting, xpath, flag_values):
        """
        Return flag helper
        :param context: converter Context
        :type context: Context
        :param setting: related setting (Release|Win32, Debug|x64,...)
        :type setting: str
        :param xpath: xpath of wanted setting
        :type xpath: str
        :param flag_values: flag values for given setting
        :type flag_values: dict
        :return: correspongin flag text of setting
        :rtype: str
        """

        flag_element = context.vcxproj['tree'].xpath(xpath, namespaces=context.vcxproj['ns'])

        values = None
        if default_value in flag_values:
            values = flag_values[default_value]

        flag_text = ''
        if flag_element:
            flag_text = flag_element[0].text
            if flag_text in flag_values:
                values = flag_values[flag_text]

        flags_message = {}
        if values is not None:
            for key in values:
                value = values[key]
                if key not in context.settings[setting]:
                    context.settings[setting][key] = []
                context.settings[setting][key].append(value)
                flags_message[key] = value

        if flags_message:
            flag_name = xpath.split(':')[-1]
            message('{0} for {1} is {2} '.format(flag_name, setting, flags_message), '')

        return flag_text

    def set_whole_program_optimization(self, context):
        """
        Set Whole Program Optimization flag: /GL and /LTCG

        """

        flag_values = {'true': {ln_flags: '/LTCG', cl_flags: '/GL'}}

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:WholeProgramOptimization'
                          .format(context.property_groups[setting]), flag_values)

    def set_link_incremental(self, context):
        """
        Set LinkIncremental flag: /INCREMENTAL

        """

        flag_values = {
            'true': {ln_flags: '/INCREMENTAL'},
            'false': {ln_flags: '/INCREMENTAL:NO'},
            default_value: {}
        }

        for setting in context.settings:
            conf_type = get_configuration_type(setting, context)
            if conf_type and 'StaticLibrary' in conf_type:
                continue
            value = self.set_flag(context, setting, '{0}/ns:LinkIncremental'
                                  .format(context.property_groups[setting]
                                          .replace(' and @Label="Configuration"', '')
                                          ), flag_values
                                  )
            if not value:
                value = self.set_flag(context, setting,
                                      '//ns:LinkIncremental[@Condition="\''
                                      '$(Configuration)|$(Platform)\'==\'{0}\'"]'
                                      .format(setting), flag_values
                                      )
            if not value:
                context.settings[setting][ln_flags].append('/INCREMENTAL')  # default

    def set_force_conformance_in_for_loop_scope(self, context):
        """
        Set flag: ForceConformanceInForLoopScope

        """

        flag_values = {
            'true': {cl_flags: '/Zc:forScope'},
            'false': {cl_flags: '/Zc:forScope-'},
            default_value: {cl_flags: '/Zc:forScope'}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:ForceConformanceInForLoopScope'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_remove_unreferenced_code_data(self, context):
        """
        Set flag: RemoveUnreferencedCodeData

        """

        flag_values = {
            'true': {cl_flags: '/Zc:inline'},
            'false': {cl_flags: ''},
            default_value: {cl_flags: '/Zc:inline'}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:RemoveUnreferencedCodeData'
                          .format(context.definition_groups[setting]), flag_values
                          )

    @staticmethod
    def set_use_debug_libraries(context):
        """
        Set Use Debug Libraries flag: /MD

        """
        for setting in context.settings:
            md = context.vcxproj['tree'].xpath(
                '{0}/ns:UseDebugLibraries'.format(context.property_groups[setting]),
                namespaces=context.vcxproj['ns']
            )
            if md:
                if 'true' in md[0].text:
                    context.settings[setting]['use_debug_libs'] = True
                else:
                    context.settings[setting]['use_debug_libs'] = False
                message('UseDebugLibrairies for {0}'.format(setting), '')
            else:
                message('No UseDebugLibrairies for {0}'.format(setting), '')

    def set_warning_level(self, context):
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

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:WarningLevel'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_warning_as_errors(self, context):
        """
        Set TreatWarningAsError: /WX

        """
        flag_values = {
            'true': {cl_flags: '/WX'},
            'false': {},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:TreatWarningAsError'
                          .format(context.definition_groups[setting]),
                          flag_values
                          )

    @staticmethod
    def set_disable_specific_warnings(context):
        """
        Set DisableSpecificWarnings: /wd*

        """
        for setting in context.settings:
            specific_warnings_node = context.vcxproj['tree'].xpath(
                '{0}/ns:ClCompile/ns:DisableSpecificWarnings'.format(
                    context.definition_groups[setting]), namespaces=context.vcxproj['ns']
            )
            if specific_warnings_node:
                flags = []
                for sw in specific_warnings_node[0].text.strip().split(";"):
                    sw = sw.strip()
                    if sw != '%(DisableSpecificWarnings)':
                        flag = '/wd{0}'.format(sw)
                        flags.append(flag)
                        context.settings[setting][cl_flags].append(flag)
                message('DisableSpecificWarnings for {0} : {1}'.format(setting, ';'.join(flags)),
                        '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    @staticmethod
    def set_additional_options(context):
        """
        Set Additional options

        """
        for setting in context.settings:
            add_opts_node = context.vcxproj['tree'].xpath(
                '{0}/ns:ClCompile/ns:AdditionalOptions'.format(
                    context.definition_groups[setting]), namespaces=context.vcxproj['ns']
            )
            if add_opts_node:
                add_opts = set_unix_slash(add_opts_node[0].text).split()
                ready_add_opts = []
                for opt in add_opts:
                    if opt != '%(AdditionalOptions)':
                        context.settings[setting][cl_flags].append(opt)
                        ready_add_opts.append(opt)
                message('Additional Options for {0} : {1}'.format(setting, ready_add_opts), '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    def set_basic_runtime_checks(self, context):
        """
        Set Basic Runtime Checks flag: /RTC*

        """
        flag_values = {
            'StackFrameRuntimeCheck': {cl_flags: '/RTCs'},
            'UninitializedLocalUsageCheck': {cl_flags: '/RTCu'},
            'EnableFastChecks': {cl_flags: '/RTC1'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:BasicRuntimeChecks'
                          .format(context.definition_groups[setting]), flag_values
                          )

    @staticmethod
    def set_runtime_library(context):
        """
        Set RuntimeLibrary flag: /MDd

        """

        # RuntimeLibrary
        for setting in context.settings:
            mdd_value = context.vcxproj['tree'].find(
                '{0}/ns:ClCompile/ns:RuntimeLibrary'.format(context.definition_groups[setting]),
                namespaces=context.vcxproj['ns']
            )
            mdd = '/MDd'
            m_d = '/MD'
            mtd = '/MTd'
            m_t = '/MT'

            if 'use_debug_libs' in context.settings[setting]:
                if context.settings[setting]['use_debug_libs']:
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
                message('RuntimeLibrary {0} for {1} is {2}'
                        .format(mdd_value.text, setting, cl_flag_value), '')
            else:
                cl_flag_value = m_d  # TODO: investigate what is default?
                message('Default RuntimeLibrary {0} for {1} but may be error. Check!'
                        .format(m_d, setting), 'warn')

            if cl_flag_value:
                context.settings[setting][cl_flags].append(cl_flag_value)

    def set_string_pooling(self, context):
        """
        Set StringPooling flag: /GF

        """
        flag_values = {
            'true': {cl_flags: '/GF'},
            'false': {cl_flags: '/GF-'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:StringPooling'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_optimization(self, context):
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

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:Optimization'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_inline_function_expansion(self, context):
        """
        Set Inline Function Expansion flag: /Ob

        """
        flag_values = {
            'Disabled': {cl_flags: '/Ob0'},
            'OnlyExplicitInline': {cl_flags: '/Ob1'},
            'AnySuitable': {cl_flags: '/Ob2'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:InlineFunctionExpansion'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_intrinsic_functions(self, context):
        """
        Set Intrinsic Functions flag: /Oi

        """
        flag_values = {
            'true': {cl_flags: '/Oi'},
            'false': {},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:IntrinsicFunctions'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_runtime_type_info(self, context):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        flag_values = {
            'true': {cl_flags: '/GR'},
            'false': {},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:RuntimeTypeInfo'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_function_level_linking(self, context):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        flag_values = {
            'true': {cl_flags: '/Gy'},
            'false': {},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:FunctionLevelLinking'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_debug_information_format(self, context):
        """
        Set GenerateDebugInformation flag: /Zi

        """
        flag_values = {
            'ProgramDatabase': {cl_flags: '/Zi'},
            'EditAndContinue': {cl_flags: '/ZI'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:DebugInformationFormat'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_compile_as(self, context):
        """
        Set Compile As flag: /TP, TC

        """
        flag_values = {
            'CompileAsCpp': {cl_flags: '/TP'},
            'CompileAsC': {cl_flags: '/TC'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:CompileAs'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_generate_debug_information(self, context):
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

        for setting in context.settings:
            conf_type = get_configuration_type(setting, context)
            if conf_type and 'StaticLibrary' in conf_type:
                continue

            self.set_flag(context, setting,
                          '{0}/ns:Link/ns:GenerateDebugInformation'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_floating_point_model(self, context):
        """
        Set FloatingPointModel flag: /fp

        """
        flag_values = {
            'Precise': {cl_flags: '/fp:precise'},
            'Strict': {cl_flags: '/fp:strict'},
            'Fast': {cl_flags: '/fp:fast'},
            default_value: {cl_flags: '/fp:precise'}
        }

        for setting in context.settings:
            self.set_flag(context, setting, '{0}/ns:ClCompile/ns:FloatingPointModel'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_exception_handling(self, context):
        """
        Set ExceptionHandling flag: /EHsc

        """
        flag_values = {
            'false': {},
            'true': {cl_flags: '/EHsc'},
            'Async': {cl_flags: '/EHa'},
            default_value: {cl_flags: '/EHsc'}
        }

        for setting in context.settings:
            self.set_flag(context, setting, '{0}/ns:ClCompile/ns:ExceptionHandling'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_buffer_security_check(self, context):
        """
        Set BufferSecurityCheck flag: /GS

        """
        flag_values = {
            'false': {},
            'true': {cl_flags: '/GS'},
            default_value: {cl_flags: '/GS'}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:BufferSecurityCheck'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_diagnostics_format(self, context):
        """
        Set DiagnosticsFormat flag : /GS

        """
        flag_values = {
            'Classic': {cl_flags: '/diagnostics:classic'},
            'Column': {cl_flags: '/diagnostics:column'},
            'Caret': {cl_flags: '/diagnostics:caret'},
            default_value: {cl_flags: '/diagnostics:classic'}
        }

        for setting in context.settings:
            self.set_flag(context, setting,
                          '{0}/ns:ClCompile/ns:DiagnosticsFormat'
                          .format(context.definition_groups[setting]), flag_values
                          )

    def set_disable_language_extensions(self, context):
        """
                Set DisableLanguageExtensions /Za

        """
        flag_values = {
            'false': {},
            'true': {cl_flags: '/Za'},
            default_value: {}
        }

        for setting in context.settings:
            self.set_flag(context,
                          setting,
                          '{0}/ns:ClCompile/ns:DisableLanguageExtensions'.format(
                              context.definition_groups[setting]),
                          flag_values
                          )

    def set_treatwchar_t_as_built_in_type(self, context):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        flag_values = {
            'false': {cl_flags: '/Zc:wchar_t-'},
            'true': {cl_flags: '/Zc:wchar_t'},
            default_value: {cl_flags: '/Zc:wchar_t'}
        }

        for setting in context.settings:
            self.set_flag(context,
                          setting,
                          '{0}/ns:ClCompile/ns:TreatWChar_tAsBuiltInType'.format(
                              context.definition_groups[setting]),
                          flag_values
                          )

    @staticmethod
    def setting_has_pch(context, setting):
        """
        Return if there is precompiled header or not for given setting

        :param context: converter Context
        :type context: Context
        :param setting: related setting (Release|x64, Debug|Win32,...)
        :type setting: str
        :return: if use PCH or not
        :rtype: bool
        """

        has_pch = context.settings[setting]['PrecompiledHeader']

        return 'Use' in has_pch

    def write_precompiled_headers_macro(self, context, cmake_file):
        """
        Write Precompiled header macro (only for MSVC compiler)

        :param context: converter Context
        :type context: Context
        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        need_pch_macro = False
        for setting in context.settings:
            if self.setting_has_pch(context, setting):
                need_pch_macro = True
                break

        if need_pch_macro:
            cmake_file.write(pch_macro_text)

    @staticmethod
    def write_precompiled_headers(context, setting, cmake_file):
        """
        Write precompiled headers, if needed, on given CMake file

        :param context: converter Context
        :type context: Context
        :param setting: related setting (Release|x64, Debug|Win32,...)
        :type setting: str
        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        pch_header = context.settings[setting]['PrecompiledHeaderFile']
        pch_source = context.settings[setting]['PrecompiledSourceFile']
        working_path = os.path.dirname(context.vcxproj_path)
        cmake_file.write(
            'ADD_PRECOMPILED_HEADER("{0}" "{1}" SRC_FILES)\n\n'.format(
                os.path.basename(pch_header), normalize_path(working_path, pch_source)
            )
        )

    def write_use_pch_macro(self, context, cmake_file):
        setting = ''
        for s in context.settings:
            setting = s

        cmake_file.write('# Warning: pch and target are the same for every configuration\n')
        if self.setting_has_pch(context, setting):
            self.write_precompiled_headers(context, setting, cmake_file)

    @staticmethod
    def write_target_artifact(context, cmake_file):
        """
        Add Library or Executable target

        :param context: converter Context
        :type context: Context
        :param cmake_file: CMakeLIsts.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        configuration_type = None
        for s in context.settings:
            configuration_type = get_configuration_type(s, context)
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
            if not context.has_only_headers:
                cmake_file.write(' ${SRC_FILES}')
            if context.has_headers:
                cmake_file.write(' ${HEADERS_FILES}')
            cmake_file.write(')\n\n')


class FortranFlags(Flags):
    """
        Class who check and create compilation flags for Fortran compiler
    """

    @staticmethod
    def set_flag(context, node, attr, flag_values):
        """
        Set flag helper

        :param context: converter Context
        :type context: Context
        :param node:
        :param attr:
        :param flag_values:
        :return:
        """

        for setting in context.settings:
            values = None
            if default_value in flag_values:
                values = flag_values[default_value]

            # flag_text = ''
            flag_text = context.settings[setting][node].get(attr)
            if flag_text in flag_values:
                values = flag_values[flag_text]

            flags_message = {}
            if values is not None:
                for key in values:
                    value = values[key]
                    if key not in context.settings[setting]:
                        context.settings[setting][key] = []
                    context.settings[setting][key].append(value)
                    flags_message[key] = value

            if flags_message:
                message('{0} for {1} is {2} '.format(attr, setting, flags_message), '')

    def define_flags(self, context):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        for setting in context.settings:
            context.settings[setting][ifort_cl_win] = []
            context.settings[setting][ifort_cl_unix] = []
            context.settings[setting][ifort_ln] = []

        self.set_suppress_startup_banner(context)
        self.set_debug_information_format(context)
        self.set_optimization(context)
        self.set_preprocess_source_file(context)
        self.set_source_file_format(context)
        self.set_debug_parameter(context)
        self.set_default_inc_and_use_path(context)
        self.set_fixed_form_line_length(context)
        self.set_open_mp(context)
        self.set_disable_specific_diagnostics(context)
        self.set_diagnostics(context)
        self.set_real_kind(context)
        self.set_local_variable_storage(context)
        self.set_init_local_var_to_nan(context)
        self.set_floating_point_exception_handling(context)
        self.set_extend_single_precision_constants(context)
        self.set_external_name_interpretation(context)
        self.set_string_length_arg_passing(context)
        self.set_external_name_underscore(context)
        self.set_traceback(context)
        self.set_runtime_checks(context)
        self.set_arg_temp_created_check(context)
        self.set_runtime_library(context)
        self.set_disable_default_lib_search(context)
        self.set_additional_options(context)

        self.set_assume_with_params(context)

    @staticmethod
    def set_assume_with_params(context):
        for setting in context.settings:
            current_setting = context.settings[setting]
            if 'assume_args' in current_setting:
                args = current_setting['assume_args']
                current_setting[ifort_cl_win].append('-assume:' + ','.join(args))
                current_setting[ifort_cl_unix].append('-assume ' + ','.join(args))

    def set_external_name_underscore(self, context):
        flag_values = {
            'true': {'assume_args': 'underscore'},
            'false': {'assume_args': 'nounderscore'},
            default_value: {'assume_args': 'nounderscore'}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'ExternalNameUnderscore', flag_values)

    def set_external_name_interpretation(self, context):
        flag_values = {
            'extNameUpperCase': {ifort_cl_win: '-names:uppercase',
                                 ifort_cl_unix: '-names uppercase'},
            'extNameLowerCase': {ifort_cl_win: '-names:lowercase',
                                 ifort_cl_unix: '-names lowercase'},
            'extNameAsIs': {ifort_cl_win: '-names:as_is',
                            ifort_cl_unix: '-names as_is'},
            default_value: {ifort_cl_win: '-names:uppercase',
                            ifort_cl_unix: '-names lowercase'}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'ExternalNameInterpretation', flag_values)

    def set_diagnostics(self, context):
        flag_values = {
            'diagnosticsShowAll': {ifort_cl_win: '-warn:all',
                                   ifort_cl_unix: '-warn all'},
            'diagnosticsDisableAll': {ifort_cl_win: '-warn:none',
                                      ifort_cl_unix: '-warn none'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'Diagnostics', flag_values)

    def set_arg_temp_created_check(self, context):
        """
        """
        flag_values = {
            'true': {ifort_cl_win: '-check:arg_temp_created',
                     ifort_cl_unix: '-check arg_temp_created'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'ArgTempCreatedCheck', flag_values)

    def set_debug_parameter(self, context):
        """
        """
        flag_values = {
            'debugParameterAll': {ifort_cl_win: '-debug-parameters:all',
                                  ifort_cl_unix: '-debug-parameters all'},
            'debugParameterUsed': {ifort_cl_win: '-debug-parameters:used',
                                   ifort_cl_unix: '-debug-parameters used'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'DebugParameter', flag_values)

    def set_fixed_form_line_length(self, context):
        """
        Set fixed form line length

        """
        flag_values = {
            'fixedLength80': {ifort_cl_win: '-extend-source:80',
                              ifort_cl_unix: '-extend-source 80'},
            'fixedLength132': {ifort_cl_win: '-extend-source:132',
                               ifort_cl_unix: '-extend-source 132'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'FixedFormLineLength', flag_values)

    def set_default_inc_and_use_path(self, context):
        """
        Set default include and path

        """

        flag_values = {
            'defaultIncludeCurrent': {'assume_args': 'nosource_include'},
            default_value: {'assume_args': 'source_include'}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'DefaultIncAndUsePath', flag_values)

    def set_open_mp(self, context):
        """
        Set open MP flag

        """
        flag_values = {
            'OpenMPParallelCode': {ifort_cl_win: '-Qopenmp',
                                   ifort_cl_unix: '-qopenmp'},
            'OpenMPSequentialCode': {ifort_cl_win: '-Qopenmp-stubs',
                                     ifort_cl_unix: '-qopenmp-stubs'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'OpenMP', flag_values)

    @staticmethod
    def set_disable_specific_diagnostics(context):
        """
        Set disable specific diagnostic flag

        """

        for setting in context.settings:
            # TODO: split list
            opt = context.settings[setting]['VFFortranCompilerTool']\
                .get('DisableSpecificDiagnostics')
            if opt:
                context.settings[setting][ifort_cl_win].append('-Qdiag-disable:{0}'.format(opt))
                context.settings[setting][ifort_cl_unix].append('-diag-disable={0}'.format(opt))

    def set_string_length_arg_passing(self, context):
        """
        Set string lengh arg parsing

        """
        flag_values = {
            'strLenArgsMixed': {ifort_cl_win: '-iface:mixed_str_len_arg'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'StringLengthArgPassing', flag_values)

    def set_runtime_library(self, context):
        """
        Set runtime library flag

        """
        flag_values = {
            'rtMultiThreadedDLL': {ifort_cl_win: '-libs:dll;-threads',
                                   ifort_cl_unix: '-threads'},
            'rtQuickWin': {ifort_cl_win: '-libs:qwin'},
            'rtStandardGraphics': {ifort_cl_win: '-libs:qwins'},
            'rtMultiThreadedDebug': {ifort_cl_win: '-libs:static;-threads;-dbglibs',
                                     ifort_cl_unix: '-threads'},
            'rtMultiThreadedDebugDLL': {ifort_cl_win: '-libs:dll;-threads;-dbglibs',
                                        ifort_cl_unix: '-threads'},
            'rtQuickWinDebug': {ifort_cl_win: '-libs:qwin;-dbglibs'},
            'rtStandardGraphicsDebug': {ifort_cl_win: '-libs:qwins;-dbglibs'},
            default_value: {ifort_cl_win: '-libs:static;-threads',
                            ifort_cl_unix: '-threads'}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'RuntimeLibrary', flag_values)

    def set_disable_default_lib_search(self, context):
        """
        Set disable default lib search

        """
        flag_values = {
            'true': {ifort_cl_win: '-libdir:noauto'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'DisableDefaultLibSearch', flag_values)

    def set_runtime_checks(self, context):
        """
        Set runtime checks flag

        """
        flag_values = {
            'rtChecksAll': {ifort_cl_win: '-check:all',
                            ifort_cl_unix: '-check all'},
            'rtChecksNone': {ifort_cl_win: '-nocheck',
                             ifort_cl_unix: '-nocheck'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'RuntimeChecks', flag_values)

    def set_traceback(self, context):
        """
        Set traceback flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-traceback',
                     ifort_cl_unix: '-traceback'},
            'false': {ifort_cl_win: '-notraceback',
                      ifort_cl_unix: '-notraceback'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'Traceback', flag_values)

    def set_extend_single_precision_constants(self, context):
        """
        Set extend single precision constants flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-fpconstant',
                     ifort_cl_unix: '-fpconstant'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'ExtendSinglePrecisionConstants',
                      flag_values)

    def set_floating_point_exception_handling(self, context):
        """
        Set floating exception handling

        """
        flag_values = {
            'fpe0': {ifort_cl_win: '-fpe0',
                     ifort_cl_unix: '-fpe0'},
            'fpe1': {ifort_cl_win: '-fpe1',
                     ifort_cl_unix: '-fpe1'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'FloatingPointExceptionHandling',
                      flag_values)

    def set_init_local_var_to_nan(self, context):
        """
        Set init local var to NaN flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-Qtrapuv',
                     ifort_cl_unix: '-ftrapuv'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'InitLocalVarToNAN', flag_values)

    def set_preprocess_source_file(self, context):
        """
        Set preprocess source file flag

        """
        flag_values = {
            'preprocessYes': {ifort_cl_win: '-fpp',
                              ifort_cl_unix: '-fpp'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'Preprocess', flag_values)

    def set_optimization(self, context):
        """
        Set optimization flag

        """
        flag_values = {
            'optimizeMinSpace': {ifort_cl_win: '-O1',
                                 ifort_cl_unix: '-O1'},
            'optimizeFull': {ifort_cl_win: '-O3',
                             ifort_cl_unix: '-O3'},
            'optimizeDisabled': {ifort_cl_win: '-Od'},
            default_value: {ifort_cl_win: '-O2',
                            ifort_cl_unix: '-O2'}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'Optimization', flag_values)

    def set_debug_information_format(self, context):
        """
        Set debug inforamtion format flag

        """
        flag_values = {
            'debugEnabled': {ifort_cl_win: '-debug:full',
                             ifort_cl_unix: '-debug full'},
            'debugLineInfoOnly': {ifort_cl_win: '-debug:minimal',
                                  ifort_cl_unix: '-debug minimal'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'DebugInformationFormat', flag_values)

    def set_suppress_startup_banner(self, context):
        """
        Set supress banner flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-nologo'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'SuppressStartupBanner', flag_values)

    def set_source_file_format(self, context):
        """
        Set source file format flag

        """
        flag_values = {
            'fileFormatFree': {ifort_cl_win: '-free',
                               ifort_cl_unix: '-free'},
            'fileFormatFixed': {ifort_cl_win: '-fixed',
                                ifort_cl_unix: '-fixed'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'SourceFileFormat', flag_values)

    def set_local_variable_storage(self, context):
        """
        Set local variable storage flag

        """
        flag_values = {
            'localStorageAutomatic': {ifort_cl_win: '-Qauto',
                                      ifort_cl_unix: '-auto'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'LocalVariableStorage', flag_values)

    def set_real_kind(self, context):
        """
        Set real kind flag

        """
        flag_values = {
            'realKIND8': {ifort_cl_win: '-real-size:64',
                          ifort_cl_unix: '-real-size 64'},
            'realKIND16': {ifort_cl_win: '-real-size:128',
                           ifort_cl_unix: '-real-size 128'},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'RealKIND', flag_values)

    @staticmethod
    def set_additional_options(context):
        """
        Set Additional options

        """
        for setting in context.settings:
            add_opts = context.settings[setting]['VFFortranCompilerTool'].get('AdditionalOptions')
            if add_opts:
                add_opts = set_unix_slash(add_opts).split()
                ready_add_opts = []
                for add_opt in add_opts:
                    add_opt = add_opt.strip()
                    if '/Qprof-dir' in add_opt:
                        name_value = add_opt.split(':')
                        add_opt = name_value[0] + ':' + normalize_path(
                            os.path.dirname(context.vcxproj_path), name_value[1]
                        )

                    add_opt = '-' + add_opt[1:]
                    ready_add_opts.append(add_opt)
                    unix_option = add_opt.replace(':', ' ')
                    if 'gen-interfaces' in unix_option:
                        pass
                    elif 'Qprec-div' in unix_option:
                        unix_option = unix_option.replace('Qprec-div', 'prec-div')
                    elif '-static' == unix_option:
                        pass
                    elif 'Qprof-dir' in unix_option:
                        unix_option = unix_option.replace('Qprof-dir', 'prof-dir')
                    elif 'Qprof-use' in unix_option:
                        unix_option = unix_option.replace('Qprof-use', 'prof-use')
                    else:
                        message('Unix ifort option "{0}" may be incorrect. '
                                'Check it and set it with visual studio UI if possible.'
                                .format(unix_option), 'warn')
                    context.settings[setting][ifort_cl_win].append(add_opt)
                    context.settings[setting][ifort_cl_unix].append(unix_option)
                message('Additional Options for {0} : {1}'.format(setting, str(ready_add_opts)), '')
            else:
                message('No Additional Options for {0}'.format(setting), '')

    @staticmethod
    def write_target_artifact(context, cmake_file):
        """
        Add Library or Executable target

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message('CMake will build a STATIC Library.', '')
        cmake_file.write('add_library(${PROJECT_NAME} STATIC')
        cmake_file.write(' ${SRC_FILES}')
        cmake_file.write(')\n\n')
