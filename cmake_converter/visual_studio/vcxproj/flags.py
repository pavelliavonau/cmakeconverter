#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Matthieu Estrada, ttamalfor@gmail.com
#   Pavel Liavonau, liavonlida@gmail.com
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

import re
import os

from cmake_converter.flags import *
from cmake_converter.utils import take_name_from_list_case_ignore, normalize_path
from cmake_converter.utils import set_unix_slash


class NodeStub:
    def __init__(self, flag_name):
        self.text = ''
        self.tag = flag_name


class CPPFlags(Flags):
    """
        Class who check and create compilation flags
    """

    available_std = ['c++11', 'c++14', 'c++17']

    def __init__(self):
        self.flags = {}
        self.unicode_defines = {}
        self.flags_handlers = {
            # from property_groups
            #   compilation
            'UseDebugLibraries': self.set_use_debug_libraries,
            'WholeProgramOptimization': self.set_whole_program_optimization,
            #   linking 
            'GenerateDebugInformation': self.set_generate_debug_information,
            'LinkIncremental': self.set_link_incremental,    
            # from definition_groups
            #   compilation
            'Optimization': self.set_optimization,
            'InlineFunctionExpansion': self.set_inline_function_expansion,
            'IntrinsicFunctions': self.set_intrinsic_functions,
            'StringPooling': self.set_string_pooling,
            'BasicRuntimeChecks': self.set_basic_runtime_checks,
            'RuntimeLibrary': self.set_runtime_library,
            'FunctionLevelLinking': self.set_function_level_linking,
            'WarningLevel': self.set_warning_level,
            'TreatWarningAsError': self.set_warning_as_errors,
            'DebugInformationFormat': self.set_debug_information_format,
            'CompileAs': self.set_compile_as,
            'FloatingPointModel': self.set_floating_point_model,
            'RuntimeTypeInfo': self.set_runtime_type_info,
            'DisableSpecificWarnings': self.set_disable_specific_warnings,
            'CompileAdditionalOptions': self.set_compile_additional_options,
            'LinkAdditionalOptions': self.set_link_additional_options,
            'ExceptionHandling': self.set_exception_handling,
            'BufferSecurityCheck': self.set_buffer_security_check,
            'DiagnosticsFormat': self.set_diagnostics_format,
            'DisableLanguageExtensions': self.set_disable_language_extensions,
            'TreatWChar_tAsBuiltInType': self.set_treatwchar_t_as_built_in_type,
            'ForceConformanceInForLoopScope': self.set_force_conformance_in_for_loop_scope,
            'RemoveUnreferencedCodeData': self.set_remove_unreferenced_code_data,
            'OpenMPSupport': self.set_openmp_support,
            'PrecompiledHeader': self.do_precompiled_headers,
        }

    def __set_default_flags(self, context):
        if context.current_setting not in self.flags:
            self.flags[context.current_setting] = {}
        for flag_name in self.__get_result_order_of_flags():
            self.flags[context.current_setting][flag_name] = {}
            stub = NodeStub(flag_name)
            self.set_flag(context, stub)

    @staticmethod
    def __get_result_order_of_flags():
        flags_list = [
            'UseDebugLibraries',
            'WholeProgramOptimization',
            'GenerateDebugInformation',
            'LinkIncremental',
            'Optimization',
            'InlineFunctionExpansion',
            'IntrinsicFunctions',
            'StringPooling',
            'BasicRuntimeChecks',
            'RuntimeLibrary',
            'FunctionLevelLinking',
            'WarningLevel',
            'TreatWarningAsError',
            'DebugInformationFormat',
            'CompileAs',
            'FloatingPointModel',
            'RuntimeTypeInfo',
            'DisableSpecificWarnings',
            'CompileAdditionalOptions',
            'LinkAdditionalOptions',
            'ExceptionHandling',
            'BufferSecurityCheck',
            'DiagnosticsFormat',
            'DisableLanguageExtensions',
            'TreatWChar_tAsBuiltInType',
            'ForceConformanceInForLoopScope',
            'RemoveUnreferencedCodeData',
            'OpenMPSupport',
            'PrecompiledHeader',
        ]
        return flags_list

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
                message(context, 'Cmake will use C++ std {0}.'.format(context.std), 'info')
                linux_flags = '-std=%s' % context.std
            else:
                message(
                    context,
                    'C++ std {0} version does not exist. CMake will use "c++11" instead'
                    .format(context.std),
                    'warn'
                )
                linux_flags = '-std=c++11'
        else:
            message(context,
                    'No C++ std version specified. CMake will use "c++11" by default.', 'info')
            linux_flags = '-std=c++11'
        references = context.vcxproj['tree'].xpath('//ns:ProjectReference',
                                                   namespaces=context.vcxproj['ns'])
        if references:
            for ref in references:
                reference = str(ref.get('Include'))
                if '\\' in reference:
                    reference = set_unix_slash(reference)
                lib = os.path.splitext(os.path.basename(reference))[0]

                if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
                    linux_flags += ' -fPIC'

        cmake_file.write('if(NOT MSVC)\n')
        cmake_file.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} %s")\n' % linux_flags)
        cmake_file.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        cmake_file.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        cmake_file.write('   endif()\n')
        cmake_file.write('endif(NOT MSVC)\n\n')

    def set_defines(self, context, defines_node):
        """
        Defines preprocessor definitions in current settings

        """
        for define in defines_node.text.split(";"):
            if define != '%(PreprocessorDefinitions)' and define != 'WIN32':
                context.settings[context.current_setting][defines].append(define)
        if context.current_setting in self.unicode_defines:
            for define in self.unicode_defines[context.current_setting]:
                context.settings[context.current_setting][defines].append(define)
        message(context, 'PreprocessorDefinitions : {}'.format(
            context.settings[context.current_setting][defines]
        ), '')

    def set_character_set(self, context, character_set_node):
        if 'Unicode' in character_set_node.text:
            self.unicode_defines[context.current_setting] = ['UNICODE', '_UNICODE']
        if 'MultiByte' in character_set_node.text:
            self.unicode_defines[context.current_setting] = ['_MBCS']

    @staticmethod
    def __get_precompiled_header_node_values():
        precompiled_header_values = {
            'Use': {'PrecompiledHeader': 'Use'},
            'NotUsing': {'PrecompiledHeader': 'NotUsing',
                         cl_flags: '/Y-'},
            'Create': {'PrecompiledHeader': 'Create'},
            default_value: {'PrecompiledHeader': 'NotUsing',
                            cl_flags: '/Y-'}
        }
        return precompiled_header_values

    def do_precompiled_headers(self, context, flag_name, node):
        """
        Add precompiled headers to settings

        :param context: converter Context
        :type context: Context
        :param flag_name:
        :param node:
        """
        del flag_name
        if node.text == '':
            return {}   # default pass

        setting = context.current_setting
        precompiled_header_file_values = {default_value: {'PrecompiledHeaderFile': 'stdafx.h'}}
        flag_value = self.set_flag_old(
            context,
            setting,
            '{0}/ns:ClCompile/ns:PrecompiledHeaderFile'.format(context.definition_groups[setting]),
            precompiled_header_file_values
        )

        if flag_value:
            context.settings[setting]['PrecompiledHeaderFile'] = [flag_value]

        return self.__get_precompiled_header_node_values()

    @staticmethod
    def define_pch_cpp_file(context):
        pch_header_path = ''
        pch_source_path = ''
        for setting in context.settings:
            if 'Use' in context.settings[setting]['PrecompiledHeader'] and pch_header_path == '':
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
                if founded_pch_h_path:
                    founded_pch_h_path += '/'
                pch_header_path = founded_pch_h_path + pch_header_name

                pch_source_name = pch_header_name.replace('.h', '.cpp')
                real_pch_cpp = ''
                real_pch_cpp_path = ''
                if founded_pch_h_path in context.sources:
                    real_pch_cpp = take_name_from_list_case_ignore(
                        context,
                        context.sources[founded_pch_h_path], pch_source_name
                    )
                    real_pch_cpp_path = founded_pch_h_path
                else:
                    for src_path in context.sources:
                        for src in context.sources[src_path]:
                            if pch_source_name == src:
                                real_pch_cpp = take_name_from_list_case_ignore(
                                    context,
                                    context.sources[src_path], src
                                )
                                real_pch_cpp_path = src_path
                if real_pch_cpp_path:
                    real_pch_cpp_path += '/'
                pch_source_path = real_pch_cpp_path + real_pch_cpp

            context.settings[setting]['PrecompiledHeaderFile'] = pch_header_path
            context.settings[setting]['PrecompiledSourceFile'] = pch_source_path

    def set_flag_old(self, context, setting, xpath, flag_values):
        """
        Return flag helper
        :param context: converter Context
        :type context: Context
        :param setting: related setting (Release|Win32, Debug|x64,...)
        :type setting: str
        :param xpath: xpath of wanted setting
        :type xpath: str
        :param flag_values: flag result_node_values for given setting
        :type flag_values: dict
        :return: corresponding flag text of setting
        :rtype: str
        """

        flag_element = context.vcxproj['tree'].xpath(xpath, namespaces=context.vcxproj['ns'])

        result_node_values = self.__get_default_flag_values(flag_values)

        flag_text, result_node_values = self.__add_flag_values_according_node_text(
            flag_values,
            flag_element,
            result_node_values
        )

        flags_message = self.__add_flag_values_to_context(context.settings, setting,
                                                          result_node_values)

        if flags_message:
            flag_name = xpath.split(':')[-1]
            message(context, '{0} for {1} is {2} '.format(flag_name, setting, flags_message), '')

        return flag_text

    def set_flag(self, context, node):
        """
        Set flag helper

        :param context: converter Context
        :type context: Context
        :param node:
        :return:
        """

        flag_name = re.sub(r'{.*\}', '', node.tag)  # strip namespace
        flag_value = node.text

        flag_values = self.flags_handlers[flag_name](context, flag_name, node)

        if flag_values is None:
            return

        values = None
        if default_value in flag_values:
            values = flag_values[default_value]

        if flag_value in flag_values:
            values = flag_values[flag_value]

        flags_message = {}
        if values is not None:
            self.flags[context.current_setting][flag_name] = {}  # reset default values
            for key in values:
                value = values[key]
                self.flags[context.current_setting][flag_name][key] = [value]
                flags_message[key] = value

        if flags_message:
            message(
                context,
                '{0} is {1} '.format(flag_name, flags_message),
                ''
            )

    def prepare_context_for_flags(self, context):
        context.settings[context.current_setting][cl_flags] = []
        context.settings[context.current_setting][ln_flags] = []
        context.settings[context.current_setting]['PrecompiledHeader'] = []
        self.__set_default_flags(context)

    def apply_flags_to_context(self, context):
        context_flags_data_keys = [
            cl_flags,
            ln_flags,
            'PrecompiledHeader',
        ]

        for setting in context.settings:
            self.apply_generate_debug_information(context, setting)
            self.apply_link_incremental(context, setting)
            self.apply_use_debug_libs(context, setting)
            for flag_name in self.__get_result_order_of_flags():
                for context_flags_data_key in context_flags_data_keys:
                    if context_flags_data_key in self.flags[setting][flag_name]:
                        for value in self.flags[setting][flag_name][context_flags_data_key]:
                            context.settings[setting][context_flags_data_key].append(
                                value
                            )
                    for file in context.file_contexts:
                        file_context = context.file_contexts[file]
                        file_flags = context.file_contexts[file].flags.flags[setting]
                        if flag_name not in file_flags:
                            continue
                        if context_flags_data_key in file_flags[flag_name]:
                            for value in file_flags[flag_name][context_flags_data_key]:
                                file_context.settings[setting][context_flags_data_key].append(
                                    value
                                )

    def apply_generate_debug_information(self, context, setting):
        conf_type = context.settings[setting]['target_type']
        if conf_type and 'StaticLibrary' in conf_type:
            self.flags[setting]['GenerateDebugInformation'][ln_flags] = ''

    def apply_link_incremental(self, context, setting):
        conf_type = context.settings[setting]['target_type']
        if conf_type and 'StaticLibrary' in conf_type:
            self.flags[setting]['LinkIncremental'][ln_flags] = ''

    @staticmethod
    def __get_default_flag_values(flag_values):
        node_values = {}
        if default_value in flag_values:
            node_values = flag_values[default_value]
        return node_values

    @staticmethod
    def __add_flag_values_according_node_text(flag_values, flag_element_node, result_node_values):
        flag_text = ''
        if flag_element_node:
            flag_text = flag_element_node[0].text
            if flag_text in flag_values:
                result_node_values = flag_values[flag_text]
        return flag_text, result_node_values

    @staticmethod
    def __add_flag_values_to_context(context_destination, setting, result_node_values):
        flags_message = {}
        if result_node_values is not None:
            for key in result_node_values:
                value = result_node_values[key]
                if key not in context_destination[setting]:
                    context_destination[setting][key] = []
                context_destination[setting][key].append(value)
                flags_message[key] = value
        return flags_message

    @staticmethod
    def set_whole_program_optimization(context, flag_name, node):
        """
        Set Whole Program Optimization flag: /GL and /LTCG

        """
        del context, flag_name, node
        flag_values = {'true': {ln_flags: '/LTCG', cl_flags: '/GL'}}

        return flag_values

    @staticmethod
    def set_link_incremental(context, flag_name, node):
        """
        Set LinkIncremental flag: /INCREMENTAL

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/INCREMENTAL'},
            'false': {ln_flags: '/INCREMENTAL:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_force_conformance_in_for_loop_scope(context, flag_name, node):
        """
        Set flag: ForceConformanceInForLoopScope

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Zc:forScope'},
            'false': {cl_flags: '/Zc:forScope-'},
            default_value: {cl_flags: '/Zc:forScope'}
        }

        return flag_values

    @staticmethod
    def set_remove_unreferenced_code_data(context, flag_name, node):
        """
        Set flag: RemoveUnreferencedCodeData

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Zc:inline'},
            'false': {cl_flags: ''},
            default_value: {cl_flags: '/Zc:inline'}
        }

        return flag_values

    @staticmethod
    def set_openmp_support(context, flag_name, node):
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/openmp'},
            'false': {cl_flags: ''},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_use_debug_libraries(context, flag_name, md):
        """
        Set Use Debug Libraries flag: /MD

        """
        del flag_name
        if not md.text:
            return

        setting = context.current_setting
        if 'true' in md.text:
            context.settings[setting]['use_debug_libs'] = True
        else:
            context.settings[setting]['use_debug_libs'] = False
        message(
            context,
            'UseDebugLibrairies : {}'.format(context.settings[setting]['use_debug_libs']),
            ''
        )

    @staticmethod
    def set_warning_level(context, flag_name, node):
        """
        Set Warning level for Windows: /W

        """
        del context, flag_name, node
        flag_values = {
            'Level1': {cl_flags: '/W1'},
            'Level2': {cl_flags: '/W2'},
            'Level3': {cl_flags: '/W3'},
            'Level4': {cl_flags: '/W4'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_warning_as_errors(context, flag_name, node):
        """
        Set TreatWarningAsError: /WX

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/WX'},
            'false': {},
            default_value: {}
        }

        return flag_values

    def set_disable_specific_warnings(self, context, flag_name, specific_warnings_node):
        """
        Set DisableSpecificWarnings: /wd*

        """
        if not specific_warnings_node.text:
            return

        flags = []
        for sw in specific_warnings_node.text.strip().split(";"):
            sw = sw.strip()
            if sw != '%(DisableSpecificWarnings)':
                flag = '/wd{0}'.format(sw)
                flags.append(flag)
        # TODO: is next check really necessary?
        if 'DisableSpecificWarnings' not in self.flags[context.current_setting]:
            self.flags[context.current_setting]['DisableSpecificWarnings'] = {}
        self.flags[context.current_setting][flag_name][cl_flags] = flags
        message(context, 'DisableSpecificWarnings : {}'.format(';'.join(flags)), '')

    def set_compile_additional_options(self, context, flag_name, add_opts_node):
        """
        Set Additional options

        """
        add_opts = set_unix_slash(add_opts_node.text).split()
        ready_add_opts = []
        for opt in add_opts:
            if opt != '%(AdditionalOptions)':
                ready_add_opts.append(opt)
        # TODO: is next check really necessary?
        if 'CompileAdditionalOptions' not in self.flags[context.current_setting]:
            self.flags[context.current_setting]['CompileAdditionalOptions'] = {}
        self.flags[context.current_setting][flag_name][cl_flags] = ready_add_opts
        message(context, 'Compile Additional Options : {}'.format(ready_add_opts), '')

    def set_link_additional_options(self, context, flag_name, add_opts_node):
        """
        Set Additional options

        """
        add_opts = set_unix_slash(add_opts_node.text).split()
        ready_add_opts = []
        for opt in add_opts:
            if opt != '%(AdditionalOptions)':
                ready_add_opts.append(opt)
        # TODO: is next check really necessary?
        if 'LinkAdditionalOptions' not in self.flags[context.current_setting]:
            self.flags[context.current_setting]['LinkAdditionalOptions'] = {}
        self.flags[context.current_setting][flag_name][ln_flags] = ready_add_opts
        message(context, 'Link Additional Options : {}'.format(ready_add_opts), '')

    @staticmethod
    def set_basic_runtime_checks(context, flag_name, node):
        """
        Set Basic Runtime Checks flag: /RTC*

        """
        del context, flag_name, node
        flag_values = {
            'StackFrameRuntimeCheck': {cl_flags: '/RTCs'},
            'UninitializedLocalUsageCheck': {cl_flags: '/RTCu'},
            'EnableFastChecks': {cl_flags: '/RTC1'},
            default_value: {}
        }

        return flag_values

    def set_runtime_library(self, context, flag_name, runtime_library_node):
        """
        Set RuntimeLibrary flag: /MDd

        """

        mdd = '/MDd'
        m_d = '/MD'
        mtd = '/MTd'
        m_t = '/MT'

        cl_flag_value = ''
        mdd_value = runtime_library_node.text
        if mdd_value:
            if 'MultiThreadedDebugDLL' == mdd_value:
                cl_flag_value = mdd
            if 'MultiThreadedDLL' == mdd_value:
                cl_flag_value = m_d
            if 'MultiThreaded' == mdd_value:
                cl_flag_value = m_t
            if 'MultiThreadedDebug' == mdd_value:
                cl_flag_value = mtd
            message(context, 'RuntimeLibrary {0} is {1}'
                    .format(mdd_value, cl_flag_value), '')
        else:
            cl_flag_value = m_d  # TODO: investigate what is default?
            message(context, 'Default RuntimeLibrary {0} but may be error. Check!'
                    .format(m_d), 'warn')

        if cl_flag_value:
            # TODO: is next check really necessary?
            if 'RuntimeLibrary' not in self.flags[context.current_setting]:
                self.flags[context.current_setting]['RuntimeLibrary'] = {}
            self.flags[context.current_setting][flag_name][cl_flags] = [cl_flag_value]

        self.apply_use_debug_libs(context, context.current_setting)

    def apply_use_debug_libs(self, context, setting):
        if 'use_debug_libs' in context.settings[setting]:
            rl_flag = self.flags[setting]['RuntimeLibrary'][cl_flags][0]
            applied_flag = rl_flag
            if context.settings[setting]['use_debug_libs']:
                if rl_flag == '/MD':
                    applied_flag = '/MDd'
                if rl_flag == '/MT':
                    applied_flag = '/MTd'
            else:
                if rl_flag == '/MDd':
                    applied_flag = '/MD'
                if rl_flag == '/MTd':
                    applied_flag = '/MT'
            self.flags[setting]['RuntimeLibrary'][cl_flags] = [applied_flag]

    @staticmethod
    def set_string_pooling(context, flag_name, node):
        """
        Set StringPooling flag: /GF

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/GF'},
            'false': {cl_flags: '/GF-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_optimization(context, flag_name, node):
        """
        Set Optimization flag: /Od

        """
        del context, flag_name, node
        flag_values = {
            'Disabled': {cl_flags: '/Od'},
            'MinSpace': {cl_flags: '/O1'},
            'MaxSpeed': {cl_flags: '/O2'},
            'Full': {cl_flags: '/Ox'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_inline_function_expansion(context, flag_name, node):
        """
        Set Inline Function Expansion flag: /Ob

        """
        del context, flag_name, node
        flag_values = {
            'Disabled': {cl_flags: '/Ob0'},
            'OnlyExplicitInline': {cl_flags: '/Ob1'},
            'AnySuitable': {cl_flags: '/Ob2'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_intrinsic_functions(context, flag_name, node):
        """
        Set Intrinsic Functions flag: /Oi

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Oi'},
            'false': {},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_runtime_type_info(context, flag_name, node):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/GR'},
            'false': {},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_function_level_linking(context, flag_name, node):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Gy'},
            'false': {},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_debug_information_format(context, flag_name, node):
        """
        Set DebugInformationFormat flag: /Zi

        """
        del context, flag_name, node
        flag_values = {
            'ProgramDatabase': {cl_flags: '/Zi'},
            'EditAndContinue': {cl_flags: '/ZI'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_compile_as(context, flag_name, node):
        """
        Set Compile As flag: /TP, TC

        """
        del context, flag_name, node
        flag_values = {
            'CompileAsCpp': {cl_flags: '/TP'},
            'CompileAsC': {cl_flags: '/TC'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_generate_debug_information(context, flag_name, node):
        """
        Set GenerateDebugInformation flag: /DEBUG

        """
        del context, flag_name, node
        flag_values = {
            'DebugFull': {ln_flags: '/DEBUG:FULL'},
            'DebugFastLink': {ln_flags: '/DEBUG:FASTLINK'},
            'true': {ln_flags: '/DEBUG'},
            'false': {},
            default_value: {ln_flags: '/DEBUG:FULL'}
        }

        return flag_values

    @staticmethod
    def set_floating_point_model(context, flag_name, node):
        """
        Set FloatingPointModel flag: /fp

        """
        del context, flag_name, node
        flag_values = {
            'Precise': {cl_flags: '/fp:precise'},
            'Strict': {cl_flags: '/fp:strict'},
            'Fast': {cl_flags: '/fp:fast'},
            default_value: {cl_flags: '/fp:precise'}
        }

        return flag_values

    @staticmethod
    def set_exception_handling(context, flag_name, node):
        """
        Set ExceptionHandling flag: /EHsc

        """
        del context, flag_name, node
        flag_values = {
            'false': {},
            'true': {cl_flags: '/EHsc'},
            'Async': {cl_flags: '/EHa'},
            default_value: {cl_flags: '/EHsc'}
        }

        return flag_values

    @staticmethod
    def set_buffer_security_check(context, flag_name, node):
        """
        Set BufferSecurityCheck flag: /GS

        """
        del context, flag_name, node
        flag_values = {
            'false': {cl_flags: '/GS-'},
            'true': {cl_flags: '/GS'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_diagnostics_format(context, flag_name, node):
        """
        Set DiagnosticsFormat flag : /GS

        """
        del context, flag_name, node
        flag_values = {
            'Classic': {cl_flags: '/diagnostics:classic'},
            'Column': {cl_flags: '/diagnostics:column'},
            'Caret': {cl_flags: '/diagnostics:caret'},
            default_value: {cl_flags: '/diagnostics:classic'}
        }

        return flag_values

    @staticmethod
    def set_disable_language_extensions(context, flag_name, node):
        """
        Set DisableLanguageExtensions /Za

        """
        del context, flag_name, node
        flag_values = {
            'false': {},
            'true': {cl_flags: '/Za'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def set_treatwchar_t_as_built_in_type(context, flag_name, node):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        del context, flag_name, node
        flag_values = {
            'false': {cl_flags: '/Zc:wchar_t-'},
            'true': {cl_flags: '/Zc:wchar_t'},
            default_value: {cl_flags: '/Zc:wchar_t'}
        }

        return flag_values

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
            'ADD_PRECOMPILED_HEADER("{0}" "{1}" ALL_FILES)\n\n'.format(
                os.path.basename(pch_header),
                normalize_path(context, working_path, pch_source, False)
            )
        )

    def write_use_pch_macro(self, context, cmake_file):
        need_pch_macro = False
        for setting in context.settings:
            if self.setting_has_pch(context, setting):
                need_pch_macro = True
                break

        if need_pch_macro:
            cmake_file.write('# Warning: pch and target are the same for every configuration\n')
            self.write_precompiled_headers(context, setting, cmake_file)
