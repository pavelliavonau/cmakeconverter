#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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

"""
Module that handles flags information of C/C++ projects.
"""

import re
import os
from collections import OrderedDict

from cmake_converter.flags import Flags, defines, cl_flags, default_value, ln_flags
from cmake_converter.utils import take_name_from_list_case_ignore
from cmake_converter.utils import set_unix_slash, message, replace_vs_vars_with_cmake_vars


# pylint: disable=R0903

class NodeStub:
    """ Dummy class for Node replacement """
    def __init__(self, flag_name):
        self.text = ''
        self.tag = flag_name

# pylint: enable=R0903


class CPPFlags(Flags):
    """
        Class that checks and creates compilation flags
    """

    def __init__(self):
        self.flags = {}
        self.unicode_defines = {}
        self.flags_handlers = OrderedDict([
            # compilation cl_flags
            ('ConformanceMode', self.__set_conformance_mode),
            ('MultiProcessorCompilation', self.__multi_processor_compilation),
            ('SupportJustMyCode', self.__set_support_just_my_code),
            ('LanguageStandard', self.__set_language_standard),
            ('UseDebugLibraries', self.__set_use_debug_libraries),
            ('CompileWholeProgramOptimization', self.__set_compile_whole_program_optimization),
            ('MinimalRebuild', self.__set_minimal_rebuild),
            ('Optimization', self.__set_optimization),
            ('InlineFunctionExpansion', self.__set_inline_function_expansion),
            ('IntrinsicFunctions', self.__set_intrinsic_functions),
            ('SDLCheck', self.__set_sdl_check),
            ('StringPooling', self.__set_string_pooling),
            ('EnableFiberSafeOptimizations', self.__set_enable_fiber_safe_optimizations),
            ('BasicRuntimeChecks', self.__set_basic_runtime_checks),
            ('ShowIncludes', self.__set_show_includes),
            ('CompileAsManaged', self.__set_common_language_runtime),
            ('EnableEnhancedInstructionSet', self.__set_enable_enhanced_instruction_set),
            ('OmitFramePointers', self.__set_omit_frame_pointers),
            ('CallingConvention', self.__set_calling_convention),
            ('RuntimeLibrary', self.__set_runtime_library),
            ('FunctionLevelLinking', self.__set_function_level_linking),
            ('WarningLevel', self.__set_warning_level),
            ('SuppressStartupBanner', self.__set_suppress_startup_banner),
            ('FloatingPointExceptions', self.__set_floating_point_exceptions),
            ('TreatWarningAsError', self.__set_warning_as_errors),
            ('DebugInformationFormat', self.__set_debug_information_format),
            ('AssemblerListingLocation', self.__set_assembler_listing_location),
            ('AssemblerOutput', self.__set_assembler_output),
            ('ObjectFileName', self.__set_object_file_name),
            ('FavorSizeOrSpeed', self.__set_favour_size_or_speed),
            ('CompileAs', self.__set_compile_as),
            ('FloatingPointModel', self.__set_floating_point_model),
            ('StructMemberAlignment', self.__set_struct_member_alignment),
            ('RuntimeTypeInfo', self.__set_runtime_type_info),
            ('CLRSupport', self.__set_common_language_runtime),
            ('DisableSpecificWarnings', self.__set_disable_specific_warnings),
            ('CompileAdditionalOptions', self.__set_compile_additional_options),
            ('ExceptionHandling', self.__set_exception_handling),
            ('BufferSecurityCheck', self.__set_buffer_security_check),
            ('ControlFlowGuard', self.__set_control_flow_guard),
            ('DiagnosticsFormat', self.__set_diagnostics_format),
            ('DisableLanguageExtensions', self.__set_disable_language_extensions),
            ('TreatWChar_tAsBuiltInType', self.__set_treatwchar_t_as_built_in_type),
            ('ForceConformanceInForLoopScope', self.__set_force_conformance_in_for_loop_scope),
            ('RemoveUnreferencedCodeData', self.__set_remove_unreferenced_code_data),
            ('OpenMPSupport', self.__set_openmp_support),
            ('PrecompiledHeader', self.__set_precompiled_header),
            ('PrecompiledHeaderFile', self.__set_precompiled_header_file),
            #   linking ln_flags
            ('GenerateManifest', self.__set_generate_manifest),
            ('FixedBaseAddress', self.__set_fixed_base_address),
            ('StackReserveSize', self.__set_stack_reserve_size),
            ('GenerateDebugInformation', self.__set_generate_debug_information),
            ('TargetMachine', self.__set_target_machine),
            ('ImageHasSafeExceptionHandlers', self.__set_image_has_safe_exception_handlers),
            ('IgnoreSpecificDefaultLibraries',
             self.__set_target_ignore_specific_default_libraries),
            ('SubSystem', self.__set_sub_system),
            ('OptimizeReferences', self.__set_optimize_references),
            ('LinkTimeCodeGeneration', self.__set_link_time_code_generation),
            ('EnableCOMDATFolding', self.__set_enable_comdat_folding),
            ('Profile', self.__set_profile),
            ('DataExecutionPrevention', self.__set_data_execution_prevention),
            ('RandomizedBaseAddress', self.__set_randomized_base_address),
            ('LinkIncremental', self.__set_link_incremental),
            ('IgnoreEmbeddedIDL', self.__set_ignore_embedded_idl),
            ('AssemblyDebug', self.__set_assembly_debug),
            ('LinkAdditionalOptions', self.__set_link_additional_options),
        ])

    def __set_default_flag(self, context, flag_name):
        self.flags[context.current_setting][flag_name] = {}
        stub = NodeStub(flag_name)
        self.set_flag(context, stub)

    def __set_default_flags(self, context):
        message(context, '== start making default flags ==', '')
        if context.current_setting not in self.flags:
            self.flags[context.current_setting] = {}
        for flag_name in self.flags_handlers:
            self.__set_default_flag(context, flag_name)
        message(context, '== end making default flags ==', '')

    @staticmethod
    def set_defines(context, defines_node):
        """
        Defines preprocessor definitions in current settings

        """
        for define in defines_node.text.split(";"):
            define = define.strip()
            if define != '%(PreprocessorDefinitions)':
                define = replace_vs_vars_with_cmake_vars(context, define)
                define = define.replace('\\', '\\\\')
                define = define.replace('"', '\\"')
                context.settings[context.current_setting][defines].append(define)
        message(context, 'PreprocessorDefinitions : {}'.format(
            context.settings[context.current_setting][defines]
        ), '')

    def set_character_set(self, context, character_set_node):
        """ Set defines related to selected character set """
        unicode_defines = []
        if 'Unicode' in character_set_node.text:
            unicode_defines += ['UNICODE', '_UNICODE']
        if 'MultiByte' in character_set_node.text:
            unicode_defines += ['_MBCS']
        self.unicode_defines[context.current_setting] = unicode_defines
        message(context, 'Unicode Definitions : {}'.format(unicode_defines), '')

    @staticmethod
    def __set_precompiled_header(context, flag_name, node):
        """
        Add precompiled headers to settings

        :param context: converter Context
        :type context: Context
        :param flag_name:
        :param node:
        """
        del context, flag_name
        if isinstance(node, NodeStub):
            return {}   # default pass

        precompiled_header_values = {
            'Use': {'PrecompiledHeader': 'Use'},
            'NotUsing': {'PrecompiledHeader': 'NotUsing',
                         cl_flags: '/Y-'},
            'Create': {'PrecompiledHeader': 'Create'},
            default_value: {'PrecompiledHeader': 'NotUsing',
                            cl_flags: '/Y-'}
        }
        return precompiled_header_values

    @staticmethod
    def __set_precompiled_header_file(context, flag_name, node):
        del flag_name

        pch_header_file = 'stdafx.h'  # default

        if node.text:
            pch_header_file = node.text

        context.settings[context.current_setting]['PrecompiledHeaderFile'] = pch_header_file

    @staticmethod
    def __define_pch_paths(context, setting):
        pch_header_name = context.settings[setting]['PrecompiledHeaderFile']
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
        pch_header_path = os.path.join(founded_pch_h_path, pch_header_name)

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
        pch_source_path = os.path.join(real_pch_cpp_path, real_pch_cpp)

        return pch_header_path, pch_source_path

    def define_pch_cpp_file(self, context):
        """
        Routine that evaluates PCH related stuff using project data after parsing
        """
        pch_header_path = ''
        pch_source_path = ''
        for setting in context.settings:

            if 'Use' not in context.settings[setting]['PrecompiledHeader']:
                continue

            if pch_header_path == '':
                pch_header_path, pch_source_path = self.__define_pch_paths(context, setting)

            context.settings[setting]['PrecompiledHeaderFile'] = pch_header_path
            context.settings[setting]['PrecompiledSourceFile'] = pch_source_path

    def set_flag(self, context, node):
        """
        Set flag helper

        :param context: converter Context
        :type context: Context
        :param node:
        :return:
        """

        if None in context.current_setting:
            return

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
                '{} is {} '.format(flag_name, flags_message),
                ''
            )

    def prepare_context_for_flags(self, context):
        """ Initialization of context of current setting with default flags """
        if context.current_setting not in context.flags.flags:
            context.flags.flags[context.current_setting] = {}
            self.__set_default_flags(context)

    # pylint: disable=R1702

    def apply_flags_to_context(self, context):
        """
        Routine that applies collected flags from different places to context object
        """
        context_flags_data_keys = [
            cl_flags,
            ln_flags,
            'PrecompiledHeader',
        ]

        for setting in context.settings:
            self.__apply_generate_debug_information(context, setting)
            self.__apply_link_incremental(context, setting)
            for flag_name in self.flags_handlers:
                for context_flags_data_key in context_flags_data_keys:
                    if setting in self.flags:
                        if context_flags_data_key in self.flags[setting][flag_name]:
                            for value in self.flags[setting][flag_name][context_flags_data_key]:
                                context.settings[setting][context_flags_data_key].append(
                                    value
                                )
                    for file in context.file_contexts:
                        file_context = context.file_contexts[file]
                        if setting not in context.file_contexts[file].flags.flags:
                            continue
                        file_flags = context.file_contexts[file].flags.flags[setting]
                        if flag_name not in file_flags:
                            continue
                        if context_flags_data_key in file_flags[flag_name]:
                            for value in file_flags[flag_name][context_flags_data_key]:
                                file_context.settings[setting][context_flags_data_key].append(
                                    value
                                )

            if setting in self.unicode_defines:
                for define in self.unicode_defines[setting]:
                    context.settings[setting][defines].append(define)

    # pylint: enable=R1702

    def __apply_generate_debug_information(self, context, setting):
        conf_type = context.settings[setting]['target_type']
        if conf_type and 'StaticLibrary' in conf_type:
            self.flags[setting]['GenerateDebugInformation'][ln_flags] = ''

    def __apply_link_incremental(self, context, setting):
        conf_type = context.settings[setting]['target_type']
        if conf_type and 'StaticLibrary' in conf_type:
            self.flags[setting]['LinkIncremental'][ln_flags] = ''

    @staticmethod
    def __set_compile_whole_program_optimization(context, flag_name, node):
        """
        Set Whole Program Optimization compile flag: /GL

        """
        del context, flag_name, node

        flag_values = {
            'true': {cl_flags: '/GL'},
            'false': {cl_flags: '/GL-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_link_incremental(context, flag_name, node):
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
    def __set_force_conformance_in_for_loop_scope(context, flag_name, node):
        """
        Set flag: ForceConformanceInForLoopScope

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Zc:forScope'},
            'false': {cl_flags: '/Zc:forScope-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_remove_unreferenced_code_data(context, flag_name, node):
        """
        Set flag: RemoveUnreferencedCodeData

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Zc:inline'},
            'false': {cl_flags: '/Zc:inline-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_openmp_support(context, flag_name, node):
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/openmp'},
            'false': {cl_flags: ''},
            default_value: {}
        }

        return flag_values

    def __set_use_debug_libraries(self, context, flag_name, md):
        """
        Set Use Debug Libraries flag: /MD

        It's hard to handle this with generator expressions of CMake.
        In case of issues - set flags explicitly

        """
        del context, flag_name, md

    @staticmethod
    def __set_warning_level(context, flag_name, node):
        """
        Set Warning level for Windows: /W

        """
        del context, flag_name, node
        flag_values = {
            'TurnOffAllWarnings': {cl_flags: '/w'},
            'Level1': {cl_flags: '/W1'},
            'Level2': {cl_flags: '/W2'},
            'Level3': {cl_flags: '/W3'},
            'Level4': {cl_flags: '/W4'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_suppress_startup_banner(context, flag_name, node):
        del context, flag_name

        if isinstance(node, NodeStub):  # ignore default pass
            return None

        parent = node.getparent()
        if 'ClCompile' in parent.tag:
            return {
                'true': {cl_flags: '/nologo'},
                default_value: {}
            }

        return {
            'true': {ln_flags: '/NOLOGO'},
            default_value: {}
        }

    @staticmethod
    def __set_floating_point_exceptions(context, flag_name, node):
        """
        Set FloatingPointExceptions: /fp:except

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/fp:except'},
            'false': {cl_flags: '/fp:except-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_warning_as_errors(context, flag_name, node):
        """
        Set TreatWarningAsError: /WX

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/WX'},
            'false': {cl_flags: '/WX-'},
            default_value: {}
        }

        return flag_values

    def __set_disable_specific_warnings(self, context, flag_name, specific_warnings_node):
        """
        Set DisableSpecificWarnings: /wd*

        """
        if not specific_warnings_node.text:
            return

        flags = []
        for sw in specific_warnings_node.text.split(";"):
            sw = sw.strip()
            if sw not in ('%(DisableSpecificWarnings)', ''):
                flag = '/wd{}'.format(sw)
                flags.append(flag)
        self.flags[context.current_setting][flag_name][cl_flags] = flags
        message(context, 'DisableSpecificWarnings : {}'.format(';'.join(flags)), '')

    @staticmethod
    def __set_support_just_my_code(context, flag_name, node):
        """
        Handle SupportJustMyCode
        :param context:
        :param flag_name:
        :param node:
        :return:
        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/JMC'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_conformance_mode(context, flag_name, conformance_mode_node):
        """
        Handle ConformanceMode
        :param context:
        :param flag_name:
        :param conformance_mode_node:
        :return:
        """
        del context, flag_name, conformance_mode_node
        flag_values = {
            'true': {cl_flags: '/permissive-'},
            'false': {},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __multi_processor_compilation(context, flag_name, flag_value):
        """
        Set MultiProcessorCompilation /MP

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {cl_flags: '/MP'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_language_standard(context, flag_name, language_standard_node):
        """
        Handle LanguageStandard
        :param context:
        :param flag_name:
        :param language_standard_node:
        :return:
        """
        del context, flag_name, language_standard_node
        flag_values = {
            'stdcpp14': {cl_flags: '/std:c++14'},
            'stdcpp17': {cl_flags: '/std:c++17'},
            'stdcpplatest': {cl_flags: '/std:c++latest'},
            default_value: {}
        }
        return flag_values

    def __set_compile_additional_options(self, context, flag_name, add_opts_node):
        """
        Set Additional options

        """
        add_opts = set_unix_slash(add_opts_node.text).split()
        ready_add_opts = []
        for opt in add_opts:
            if opt != '%(AdditionalOptions)':
                ready_add_opts.append(opt)
        self.flags[context.current_setting][flag_name][cl_flags] = ready_add_opts
        message(context, 'Compile Additional Options : {}'.format(ready_add_opts), '')

    def __set_link_additional_options(self, context, flag_name, add_opts_node):
        """
        Set Additional options

        """
        add_opts = set_unix_slash(add_opts_node.text).split()
        ready_add_opts = []
        for opt in add_opts:
            if opt != '%(AdditionalOptions)':
                ready_add_opts.append(opt)
        self.flags[context.current_setting][flag_name][ln_flags] = ready_add_opts
        message(context, 'Link Additional Options : {}'.format(ready_add_opts), '')

    @staticmethod
    def __set_basic_runtime_checks(context, flag_name, node):
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

    @staticmethod
    def __set_show_includes(context, flag_name, node):
        """
        Set ShowIncludes flag: /showIncludes*

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/showIncludes'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_common_language_runtime(context, flag_name, node):
        """
        Set COMMON_LANGUAGE_RUNTIME property: /clr*

        """
        del flag_name
        flag_values = {
            'Pure': 'pure',
            'Safe': 'safe',
            'true': '',
            'false': 'No'
        }

        node_text = node.text.strip()

        if node_text:
            value = flag_values[node_text]
            context.settings[context.current_setting]['COMMON_LANGUAGE_RUNTIME'] = [value]
            message(context, 'COMMON_LANGUAGE_RUNTIME : {}'.format(node_text), '')

    @staticmethod
    def __set_enable_enhanced_instruction_set(context, flag_name, node):
        """
        Set EnableEnhancedInstructionSet flag: /arch:*

        """
        del context, flag_name, node
        flag_values = {
            'StreamingSIMDExtensions': {cl_flags: '/arch:SSE'},
            'StreamingSIMDExtensions2': {cl_flags: '/arch:SSE2'},
            'AdvancedVectorExtensions': {cl_flags: '/arch:AVX'},
            'AdvancedVectorExtensions2': {cl_flags: '/arch:AVX2'},
            'NoExtensions': {cl_flags: '/arch:IA32'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_omit_frame_pointers(context, flag_name, node):
        """
        Set OmitFramePointers flag: /Oy

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Oy'},
            'false': {cl_flags: '/Oy-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_calling_convention(context, flag_name, node):
        """
        Set CallingConvention flag: /G**

        """
        del context, flag_name, node
        flag_values = {
            'Cdecl': {cl_flags: '/Gd'},
            'FastCall': {cl_flags: '/Gr'},
            'StdCall': {cl_flags: '/Gz'},
            'VectorCall': {cl_flags: '/Gv'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_runtime_library(context, flag_name, runtime_library_node):
        """
        Set RuntimeLibrary flag: /MDd

        """
        del flag_name

        node_text = runtime_library_node.text.strip()

        if node_text:
            context.settings[context.current_setting]['MSVC_RUNTIME_LIBRARY'] = [node_text]
            message(context, 'RuntimeLibrary : {}'.format(node_text), '')

    @staticmethod
    def __set_string_pooling(context, flag_name, node):
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
    def __set_enable_fiber_safe_optimizations(context, flag_name, node):
        """
        Set EnableFiberSafeOptimizations flag: /GT

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/GT'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_minimal_rebuild(context, flag_name, node):
        """
        Set MinimalRebuild flag: /Gm

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Gm'},
            'false': {cl_flags: '/Gm-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_optimization(context, flag_name, node):
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
    def __set_inline_function_expansion(context, flag_name, node):
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
    def __set_intrinsic_functions(context, flag_name, node):
        """
        Set Intrinsic Functions flag: /Oi

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Oi'},
            'false': {cl_flags: '/Oi-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_sdl_check(context, flag_name, node):
        """
        Set SDLCheck flag: /sdl

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/sdl'},
            'false': {cl_flags: '/sdl-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_runtime_type_info(context, flag_name, node):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/GR'},
            'false': {cl_flags: '/GR-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_function_level_linking(context, flag_name, node):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        del context, flag_name, node
        flag_values = {
            'true': {cl_flags: '/Gy'},
            'false': {cl_flags: '/Gy-'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_debug_information_format(context, flag_name, node):
        """
        Set DebugInformationFormat flag: /Zi

        """

        if context.file_contexts is None and node.text == '':  # if file context ignore default
            return {}

        del context, flag_name, node
        flag_values = {
            'ProgramDatabase': {cl_flags: '/Zi'},
            'EditAndContinue': {cl_flags: '/ZI'},
            default_value: {cl_flags: '${DEFAULT_CXX_DEBUG_INFORMATION_FORMAT}'}
        }

        return flag_values

    @staticmethod
    def __set_assembler_listing_location(context, flag_name, node):
        """
        Set AssemblerListingLocation flag: /Fa

        """
        del flag_name, node
        flag_values = {
            default_value: {}
        }

        # /Fa breaks non Visual Studio CMake generators.
        # In visual studio MSBuild target MakeDirsForCl creates dir before compiling but
        # other generators (Ninja, NMake Makefiles) don't.
        # Then missing target asm directory error occurs.
        # if node.text:
        #     flag_values.update(
        #         {
        #             node.text: {
        #                 cl_flags: '/Fa{}'.format(cleaning_output(context, node.text))
        #             }
        #         }
        #     )

        message(
            context,
            '/Fa option is ignored. Too hard to handle for different CMake generators.',
            'warn4',
        )

        return flag_values

    @staticmethod
    def __set_assembler_output(context, flag_name, node):
        """
        Set AssemblerOutput flag: /FA

        """
        del context, flag_name, node
        flag_values = {
            'AssemblyCode': {cl_flags: '/FA'},
            'AssemblyAndMachineCode': {cl_flags: '/FAc'},
            'AssemblyAndSourceCode': {cl_flags: '/FAs'},
            'All': {cl_flags: '/FAcs'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_object_file_name(context, flag_name, node):
        """
        Set ObjectFileName flag: /Fo

        """
        del context, flag_name, node
        flag_values = {
            default_value: {}
        }

        # /Fo is hardcoded inside CMake. No way to control this.
        # if node.text:
        #     flag_values.update(
        #         {
        #             node.text: {
        #                 cl_flags: '/Fo{}'.format(cleaning_output(context, node.text))
        #             }
        #         }
        #     )

        return flag_values

    @staticmethod
    def __set_favour_size_or_speed(context, flag_name, node):
        """
        Set FavorSizeOrSpeed: /Os, /Ot

        """
        del context, flag_name, node
        flag_values = {
            'Size': {cl_flags: '/Os'},
            'Speed': {cl_flags: '/Ot'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_compile_as(context, flag_name, node):
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
    def __set_image_has_safe_exception_handlers(context, flag_name, node):
        """
        Set ImageHasSafeExceptionHandlers flag: /SAFESEH

        """
        del context, flag_name, node
        flag_values = {
            'false': {ln_flags: '/SAFESEH:NO'},
            'true': {ln_flags: '/SAFESEH'},
            default_value: {}
        }

        return flag_values

    def __set_target_ignore_specific_default_libraries(self, context, flag_name, node):
        """
        IgnoreSpecificDefaultLibraries node handler

        :param context:
        :param node:
        :return:
        """
        del flag_name
        if node.text is None:
            return

        list_ingore_spec_libs = node.text.replace('%(IgnoreSpecificDefaultLibraries)', '')

        ignore_libs = self.get_no_default_lib_link_flags(list_ingore_spec_libs)

        if ignore_libs:
            context.settings[context.current_setting][ln_flags] += ignore_libs
            message(context, 'Ignore Specific Default Libraries : {}'.format(ignore_libs), '')

    @staticmethod
    def __set_sub_system(context, flag_name, node):
        """
        Set SubSystem flag: /SUBSYSTEM

        """
        del context, flag_name, node
        flag_values = {
            'Console': {ln_flags: '/SUBSYSTEM:CONSOLE'},
            'Windows': {ln_flags: '/SUBSYSTEM:WINDOWS'},
            'Native': {ln_flags: '/SUBSYSTEM:NATIVE'},
            'EFI Application': {ln_flags: '/SUBSYSTEM:EFI_APPLICATION'},
            'EFI Boot Service Driver': {ln_flags: '/SUBSYSTEM:EFI_BOOT_SERVICE_DRIVER'},
            'EFI ROM': {ln_flags: '/SUBSYSTEM:EFI_ROM'},
            'EFI Runtime': {ln_flags: '/SUBSYSTEM:EFI_RUNTIME_DRIVER'},
            'POSIX': {ln_flags: '/SUBSYSTEM:POSIX'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_optimize_references(context, flag_name, node):
        """
        Set OptimizeReferences flag: /OPT:REF

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/OPT:REF'},
            'false': {ln_flags: '/OPT:NOREF'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_link_time_code_generation(context, flag_name, node):
        """
        Set Link Time Code Generation flag: /LTCG

        """
        del context, flag_name, node

        flag_values = {
            'UseLinkTimeCodeGeneration': {ln_flags: '/LTCG'},
            'UseFastLinkTimeCodeGeneration': {ln_flags: '/LTCG:incremental'},
            'PGInstrument': {ln_flags: '/LTCG:PGInstrument'},
            'PGOptimization': {ln_flags: '/LTCG:PGOptimize'},
            'PGUpdate': {ln_flags: '/LTCG:PGUpdate'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_enable_comdat_folding(context, flag_name, node):
        """
        Set EnableCOMDATFolding flag: /OPT:ICF

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/OPT:ICF'},
            'false': {ln_flags: '/OPT:NOICF'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_generate_debug_information(context, flag_name, node):
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
    def __set_target_machine(context, flag_name, node):
        """
        Set TargetMachine flag: /MACHINE

        """
        del context, flag_name, node
        flag_values = {
            'MachineARM': {ln_flags: '/MACHINE:ARM'},
            'MachineARM64': {ln_flags: '/MACHINE:ARM64'},
            'MachineEBC': {ln_flags: '/MACHINE:EBC'},
            'MachineIA64': {ln_flags: '/MACHINE:IA64'},
            'MachineMIPS': {ln_flags: '/MACHINE:MIPS'},
            'MachineMIPS16': {ln_flags: '/MACHINE:MIPS16'},
            'MachineMIPSFPU': {ln_flags: '/MACHINE:MIPSFPU'},
            'MachineMIPSFPU16': {ln_flags: '/MACHINE:MIPSFPU16'},
            'MachineTHUMB': {ln_flags: '/MACHINE:THUMB'},
            'MachineX64': {ln_flags: '/MACHINE:X64'},
            'MachineX86': {ln_flags: '/MACHINE:X86'},
            'false': {},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_generate_manifest(context, flag_name, node):
        """
        Set GenerateManifest flag: /MANIFEST

        :param context:
        :param flag_name:
        :param node:
        :return:
        """

        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/MANIFEST'},
            'false': {ln_flags: '/MANIFEST:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_fixed_base_address(context, flag_name, node):
        """
        Set FixedBaseAddress flag: /FIXED

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/FIXED'},
            'false': {ln_flags: '/FIXED:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_stack_reserve_size(context, flag_name, node):
        """
        Set StackReserveSize flag: /STACK

        """
        del context, flag_name
        flag_values = {
            default_value: {}
        }

        stack_value = node.text
        if stack_value:
            flag_values.update(
                {
                    stack_value: {
                        ln_flags: '/STACK:{}'.format(stack_value)
                    }
                }
            )

        return flag_values

    @staticmethod
    def __set_profile(context, flag_name, node):
        """
        Set DataExecutionPrevention flag: /NXCOMPAT

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/PROFILE'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_data_execution_prevention(context, flag_name, node):
        """
        Set DataExecutionPrevention flag: /NXCOMPAT

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/NXCOMPAT'},
            'false': {ln_flags: '/NXCOMPAT:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_randomized_base_address(context, flag_name, node):
        """
        Set RandomizedBaseAddress flag: /DYNAMICBASE

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/DYNAMICBASE'},
            'false': {ln_flags: '/DYNAMICBASE:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_ignore_embedded_idl(context, flag_name, node):
        """
        Set IgnoreEmbeddedIDL flag: /IGNOREIDL

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/IGNOREIDL'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_assembly_debug(context, flag_name, node):
        """
        Set AssemblyDebug flag: /ASSEMBLYDEBUG

        """
        del context, flag_name, node
        flag_values = {
            'true': {ln_flags: '/ASSEMBLYDEBUG'},
            'false': {ln_flags: '/ASSEMBLYDEBUG:DISABLE'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_floating_point_model(context, flag_name, node):
        """
        Set FloatingPointModel flag: /fp

        """
        del context, flag_name, node
        flag_values = {
            'Precise': {cl_flags: '/fp:precise'},
            'Strict': {cl_flags: '/fp:strict'},
            'Fast': {cl_flags: '/fp:fast'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_struct_member_alignment(context, flag_name, node):
        """
        Set StructMemberAlignment flag: /Zp

        """
        del context, flag_name, node
        flag_values = {
            '1Byte': {cl_flags: '/Zp1'},
            '2Bytes': {cl_flags: '/Zp2'},
            '4Bytes': {cl_flags: '/Zp4'},
            '8Bytes': {cl_flags: '/Zp8'},
            '16Bytes': {cl_flags: '/Zp16'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_exception_handling(context, flag_name, node):
        """
        Set ExceptionHandling flag: /EHsc

        """
        if context.file_contexts is None and node.text == '':  # if file context ignore default
            return {}

        del context, flag_name, node
        flag_values = {
            'false': {},
            'true': {cl_flags: '/EHsc'},
            'Async': {cl_flags: '/EHa'},
            default_value: {cl_flags: '${DEFAULT_CXX_EXCEPTION_HANDLING}'}
        }

        return flag_values

    @staticmethod
    def __set_buffer_security_check(context, flag_name, node):
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
    def __set_control_flow_guard(context, flag_name, node):
        """
        Set ControlFlowGuard flag: /guard:cf

        """
        del context, flag_name, node
        flag_values = {
            'Guard': {cl_flags: '/guard:cf'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_diagnostics_format(context, flag_name, node):
        """
        Set DiagnosticsFormat flag : /diagnostics

        """
        del context, flag_name, node
        flag_values = {
            'Classic': {cl_flags: '/diagnostics:classic'},
            'Column': {cl_flags: '/diagnostics:column'},
            'Caret': {cl_flags: '/diagnostics:caret'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_disable_language_extensions(context, flag_name, node):
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
    def __set_treatwchar_t_as_built_in_type(context, flag_name, node):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        del context, flag_name, node
        flag_values = {
            'false': {cl_flags: '/Zc:wchar_t-'},
            'true': {cl_flags: '/Zc:wchar_t'},
            default_value: {}
        }

        return flag_values
