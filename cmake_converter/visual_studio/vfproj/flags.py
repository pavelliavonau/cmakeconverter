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
    Module that translates info from *.vfproj nodes into flags for compiler/linker.
"""

import os
from collections import OrderedDict

from cmake_converter.flags import Flags, default_value, ifort_cl_unix, ifort_cl_win, ifort_ln_win, \
    ifort_ln_unix
from cmake_converter.utils import normalize_path, set_unix_slash, message, cleaning_output


class FortranFlags(Flags):
    """
        Class who check and create compilation flags for Fortran compiler
    """

    def __init__(self):
        self.flags = {}
        self.flags_handlers = OrderedDict([
            ('VFFortranCompilerTool_SuppressStartupBanner', self.__set_suppress_startup_banner),
            ('VFFortranCompilerTool_MultiProcessorCompilation',
             self.__set_multi_processor_compilation),
            ('VFFortranCompilerTool_DebugInformationFormat', self.__set_debug_information_format),
            ('VFFortranCompilerTool_Optimization', self.__set_optimization),
            ('VFFortranCompilerTool_InterproceduralOptimizations',
             self.__set_interprocedural_optimizations),
            ('VFFortranCompilerTool_EnableEnhancedInstructionSet',
             self.__set_enable_enhanced_instruction_set),
            ('VFFortranCompilerTool_EnableRecursion', self.__set_enable_recursion),
            ('VFFortranCompilerTool_ReentrantCode', self.__set_reentrant_code),
            ('VFFortranCompilerTool_Preprocess', self.__set_preprocess_source_file),
            ('VFFortranCompilerTool_SourceFileFormat', self.__set_source_file_format),
            ('VFFortranCompilerTool_DebugParameter', self.__set_debug_parameter),
            ('VFFortranCompilerTool_DefaultIncAndUsePath', self.__set_default_inc_and_use_path),
            ('VFFortranCompilerTool_FixedFormLineLength', self.__set_fixed_form_line_length),
            ('VFFortranCompilerTool_OpenMP', self.__set_open_mp),
            ('VFFortranCompilerTool_DisableSpecificDiagnostics',
             self.__set_disable_specific_diagnostics),
            ('VFFortranCompilerTool_Diagnostics', self.__set_diagnostics),
            ('VFFortranCompilerTool_WarnDeclarations', self.__set_warn_declarations),
            ('VFFortranCompilerTool_WarnUnusedVariables', self.__set_warn_unused_variables),
            ('VFFortranCompilerTool_WarnIgnoreLOC', self.__set_warn_ignore_loc),
            ('VFFortranCompilerTool_WarnTruncateSource', self.__set_warn_truncate_source),
            ('VFFortranCompilerTool_WarnInterfaces', self.__set_warn_interfaces),
            ('VFFortranCompilerTool_WarnUnalignedData', self.__set_warn_unaligned_data),
            ('VFFortranCompilerTool_WarnUncalled', self.__set_warn_uncalled),
            ('VFFortranCompilerTool_SuppressUsageMessages', self.__set_suppress_usage_messages),
            ('VFFortranCompilerTool_RealKIND', self.__set_real_kind),
            ('VFFortranCompilerTool_LocalVariableStorage', self.__set_local_variable_storage),
            ('VFFortranCompilerTool_InitLocalVarToNAN', self.__set_init_local_var_to_nan),
            ('VFFortranCompilerTool_FloatingPointExceptionHandling',
             self.__set_floating_point_exception_handling),
            ('VFFortranCompilerTool_ExtendSinglePrecisionConstants',
             self.__set_extend_single_precision_constants),
            ('VFFortranCompilerTool_FloatingPointModel', self.__set_floating_point_model),
            ('VFFortranCompilerTool_FloatingPointSpeculation',
             self.__set_floating_point_speculation),
            ('VFFortranCompilerTool_FloatingPointStackCheck',
             self.__set_floating_point_stack_check),
            ('VFFortranCompilerTool_ExternalNameInterpretation',
             self.__set_external_name_interpretation),
            ('VFFortranCompilerTool_CallingConvention', self.__set_calling_convention),
            ('VFFortranCompilerTool_StringLengthArgPassing', self.__set_string_length_arg_passing),
            ('VFFortranCompilerTool_ExternalNameUnderscore', self.__set_external_name_underscore),
            ('VFFortranCompilerTool_Traceback', self.__set_traceback),
            ('VFFortranCompilerTool_RuntimeChecks', self.__set_runtime_checks),
            ('VFFortranCompilerTool_NullPointerCheck', self.__set_null_pointer_check),
            ('VFFortranCompilerTool_BoundsCheck', self.__set_bounds_check),
            ('VFFortranCompilerTool_UninitializedVariablesCheck',
             self.__set_uninitialized_variables_check),
            ('VFFortranCompilerTool_DescriptorDataTypeCheck',
             self.__set_descriptor_data_type_check),
            ('VFFortranCompilerTool_DescriptorDataSizeCheck',
             self.__set_descriptor_data_size_check),
            ('VFFortranCompilerTool_ArgTempCreatedCheck', self.__set_arg_temp_created_check),
            ('VFFortranCompilerTool_StackFrameCheck', self.__set_stack_frame_check),
            ('VFFortranCompilerTool_RuntimeLibrary', self.__set_runtime_library),
            ('VFFortranCompilerTool_DisableDefaultLibSearch',
             self.__set_disable_default_lib_search),
            ('VFFortranCompilerTool_AdditionalOptions', self.__set_additional_options),
            ('VFLinkerTool_GenerateManifest', self.__set_generate_manifest),
            ('VFLinkerTool_GenerateDebugInformation', self.__generate_debug_information),
            ('VFLinkerTool_ShowProgress', self.__show_progress),
            ('VFLinkerTool_LinkIncremental', self.__set_link_incremental),
            ('VFLinkerTool_SuppressStartupBanner', self.__set_link_suppress_startup_banner),
            ('VFLinkerTool_IgnoreDefaultLibraryNames', self.__set_ignore_default_library_names),
            ('VFLinkerTool_OptimizeReferences', self.__set_optimize_references),
            ('VFLinkerTool_EnableCOMDATFolding', self.__set_enable_comdat_folding),
            ('VFLinkerTool_TargetMachine', self.__set_target_machine),
            ('VFLinkerTool_SubSystem', self.__set_sub_system),
            ('VFLinkerTool_LinkDLL', self.__set_link_dll),
            ('VFLinkerTool_AdditionalOptions', self.__set_additional_link_options),
        ])

    def __set_default_flags(self, context):
        for flag_name in self.flags_handlers:
            self.flags[flag_name] = {}
            self.set_flag(context, flag_name, '', None)

    def set_flag(self, context, flag_name, flag_value, node):
        """
        Set flag helper

        :param context: converter Context
        :type context: Context
        :param flag_name:
        :param flag_value:
        :param node:
        :return:
        """
        del node
        if None in context.current_setting:
            return

        flag_values = self.flags_handlers[flag_name](context, flag_name, flag_value)

        if flag_values is None:
            return

        values = None
        if default_value in flag_values:
            values = flag_values[default_value]

        if flag_value in flag_values:
            values = flag_values[flag_value]

        flags_message = {}
        if values is not None:
            self.flags[flag_name] = {}  # reset default values
            for key in values:
                value = values[key]
                self.flags[flag_name][key] = [value]
                flags_message[key] = value

        if flags_message:
            message(
                context,
                '{} is {} '.format(flag_name, flags_message),
                ''
            )

    def prepare_context_for_flags(self, context):
        """ Initialize context with default state of flags """
        context.flags.flags[context.current_setting] = {}
        self.__set_default_flags(context)

    def apply_flags_to_context(self, context):
        """ Applying flags that are determined only after full pass through xml. """
        context_flags_data_keys = [
            ifort_cl_win,
            ifort_cl_unix,
            ifort_ln_win,
            ifort_ln_unix,
            'assume_args',
            'warn_args',
            'check_args'
        ]

        for flag_name in self.flags_handlers:
            for context_flags_data_key in context_flags_data_keys:
                if flag_name not in self.flags:
                    continue
                if context_flags_data_key in self.flags[flag_name]:
                    for value in self.flags[flag_name][context_flags_data_key]:
                        context.settings[context.current_setting][context_flags_data_key].append(
                            value
                        )

        self.__set_spec_options(context, 'assume_args', 'assume')
        self.__set_spec_options(context, 'check_args', 'check')
        self.__set_spec_options(context, 'warn_args', 'warn')

    @staticmethod
    def __set_spec_options(context, context_key, compiler_key):
        if context_key in context.settings[context.current_setting]:
            args = context.settings[context.current_setting][context_key]
            if args:
                context.settings[context.current_setting][ifort_cl_win].append(
                    '-{}:{}'.format(compiler_key, ','.join(args))
                )
                context.settings[context.current_setting][ifort_cl_unix].append(
                    '-{} {}'.format(compiler_key, ','.join(args))
                )

    @staticmethod
    def __set_floating_point_stack_check(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-Qfp-stack-check',
                     ifort_cl_unix: '-fp-stack-check'},
            'false': {},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_external_name_underscore(context, flag_name, flag_value):
        if context.file_contexts is None and flag_value == '':
            return {}

        del flag_name
        flag_values = {
            'true': {'assume_args': 'underscore'},
            'false': {'assume_args': 'nounderscore'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_external_name_interpretation(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'extNameUpperCase': {ifort_cl_win: '-names:uppercase',
                                 ifort_cl_unix: '-names uppercase'},
            'extNameLowerCase': {ifort_cl_win: '-names:lowercase',
                                 ifort_cl_unix: '-names lowercase'},
            'extNameAsIs': {ifort_cl_win: '-names:as_is',
                            ifort_cl_unix: '-names as_is'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_calling_convention(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'callConventionCRef': {ifort_cl_win: '-iface:cref'},
            'callConventionStdRef': {ifort_cl_win: '-iface:stdref'},
            'callConventionStdCall': {ifort_cl_win: '-iface:stdcall'},
            'callConventionCVF': {ifort_cl_win: '-iface:cvf'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_diagnostics(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'diagnosticsShowAll': {ifort_cl_win: '-warn:all',
                                   ifort_cl_unix: '-warn all'},
            'diagnosticsDisableAll': {ifort_cl_win: '-warn:none',
                                      ifort_cl_unix: '-warn none'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_declarations(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'declaration'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_unused_variables(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'unused'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_ignore_loc(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'ignore_loc'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_truncate_source(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'truncated_source'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_interfaces(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'interfaces'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_unaligned_data(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'false': {'warn_args': 'noalignments'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_warn_uncalled(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'uncalled'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_suppress_usage_messages(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {'warn_args': 'nousage'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_null_pointer_check(context, flag_name, flag_value):
        """
        Set check:pointer
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'pointer'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_bounds_check(context, flag_name, flag_value):
        """
        Set check:bounds
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'bounds'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_uninitialized_variables_check(context, flag_name, flag_value):
        """
        Set check:uninit
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'uninit'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_descriptor_data_type_check(context, flag_name, flag_value):
        """
        Set check:format
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'format'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_descriptor_data_size_check(context, flag_name, flag_value):
        """
        Set check:output_conversion
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'output_conversion'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_arg_temp_created_check(context, flag_name, flag_value):
        """
        Set check:arg_temp_created
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'arg_temp_created'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_stack_frame_check(context, flag_name, flag_value):
        """
        Set check:stack
        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {'check_args': 'stack'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_debug_parameter(context, flag_name, flag_value):
        """
        Set check:debug-parameters
        """
        del context, flag_name, flag_value
        flag_values = {
            'debugParameterAll': {ifort_cl_win: '-debug-parameters:all',
                                  ifort_cl_unix: '-debug-parameters all'},
            'debugParameterUsed': {ifort_cl_win: '-debug-parameters:used',
                                   ifort_cl_unix: '-debug-parameters used'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_fixed_form_line_length(context, flag_name, flag_value):
        """
        Set fixed form line length

        """
        del context, flag_name, flag_value
        flag_values = {
            'fixedLength80': {ifort_cl_win: '-extend-source:80',
                              ifort_cl_unix: '-extend-source 80'},
            'fixedLength132': {ifort_cl_win: '-extend-source:132',
                               ifort_cl_unix: '-extend-source 132'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_default_inc_and_use_path(context, flag_name, flag_value):
        """
        Set default include and path

        """
        del context, flag_name, flag_value
        flag_values = {
            'defaultIncludeCurrent': {'assume_args': 'nosource_include'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_open_mp(context, flag_name, flag_value):
        """
        Set open MP flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'OpenMPParallelCode': {ifort_cl_win: '-Qopenmp',
                                   ifort_cl_unix: '-qopenmp'},
            'OpenMPSequentialCode': {ifort_cl_win: '-Qopenmp-stubs',
                                     ifort_cl_unix: '-qopenmp-stubs'},
            default_value: {}
        }
        return flag_values

    def __set_disable_specific_diagnostics(self, context, flag_name, flag_value):
        """
        Set disable specific diagnostic flag

        """
        del context
        # value must be a list with ',' separator
        opt = flag_value
        if opt:
            self.flags[flag_name][ifort_cl_win] = ['-Qdiag-disable:{}'.format(opt)]
            self.flags[flag_name][ifort_cl_unix] = ['-diag-disable={}'.format(opt)]

    @staticmethod
    def __set_string_length_arg_passing(context, flag_name, flag_value):
        """
        Set string lengh arg parsing

        """
        del context, flag_name, flag_value
        flag_values = {
            'strLenArgsMixed': {ifort_cl_win: '-iface:mixed_str_len_arg',
                                ifort_cl_unix: '-mixed-str-len-arg'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_runtime_library(context, flag_name, flag_value):
        """
        Set runtime library flag

        """
        del context, flag_name, flag_value
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
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_disable_default_lib_search(context, flag_name, flag_value):
        """
        Set disable default lib search

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-libdir:noauto'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_runtime_checks(context, flag_name, flag_value):
        """
        Set runtime checks flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'rtChecksAll': {ifort_cl_win: '-check:all',
                            ifort_cl_unix: '-check all'},
            'rtChecksNone': {ifort_cl_win: '-nocheck',
                             ifort_cl_unix: '-nocheck'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_traceback(context, flag_name, flag_value):
        """
        Set traceback flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-traceback',
                     ifort_cl_unix: '-traceback'},
            'false': {ifort_cl_win: '-notraceback',
                      ifort_cl_unix: '-notraceback'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_extend_single_precision_constants(context, flag_name, flag_value):
        """
        Set extend single precision constants flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-fpconstant',
                     ifort_cl_unix: '-fpconstant'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_floating_point_model(context, flag_name, flag_value):
        """
        Set extend single precision constants flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'fast2': {ifort_cl_win: '-fp:fast=2',
                      ifort_cl_unix: '-fp-model fast=2'},
            'strict': {ifort_cl_win: '-fp:strict',
                       ifort_cl_unix: '-fp-model strict'},
            'source': {ifort_cl_win: '-fp:source',
                       ifort_cl_unix: '-fp-model source'},
            'precise': {ifort_cl_win: '-fp:precise',
                        ifort_cl_unix: '-fp-model precise'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_floating_point_speculation(context, flag_name, flag_value):
        """
        Set extend single precision constants flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'fpSpeculationSafe': {ifort_cl_win: '-Qfp-speculation:safe',
                                  ifort_cl_unix: '-fp-speculation=safe'},
            'fpSpeculationStrict': {ifort_cl_win: '-Qfp-speculation:strict',
                                    ifort_cl_unix: '-fp-speculation=strict'},
            'fpSpeculationOff': {ifort_cl_win: '-Qfp-speculation:off',
                                 ifort_cl_unix: '-fp-speculation=off'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_floating_point_exception_handling(context, flag_name, flag_value):
        """
        Set floating exception handling

        """
        del context, flag_name, flag_value
        flag_values = {
            'fpe0': {ifort_cl_win: '-fpe0',
                     ifort_cl_unix: '-fpe0'},
            'fpe1': {ifort_cl_win: '-fpe1',
                     ifort_cl_unix: '-fpe1'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_init_local_var_to_nan(context, flag_name, flag_value):
        """
        Set init local var to NaN flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-Qtrapuv',
                     ifort_cl_unix: '-ftrapuv'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_preprocess_source_file(context, flag_name, flag_value):
        """
        Set preprocess source file flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'preprocessYes': {ifort_cl_win: '-fpp',
                              ifort_cl_unix: '-fpp'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_optimization(context, flag_name, flag_value):
        """
        Set optimization flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'optimizeMinSpace': {ifort_cl_win: '-O1',
                                 ifort_cl_unix: '-O1'},
            'optimizeFull': {ifort_cl_win: '-O3',
                             ifort_cl_unix: '-O3'},
            'optimizeDisabled': {ifort_cl_win: '-Od',
                                 ifort_cl_unix: '-O0'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_interprocedural_optimizations(context, flag_name, flag_value):
        """
        Set InterproceduralOptimizations

        """
        del flag_name, flag_value

        target_type = context.settings[context.current_setting]['target_type']
        fat_lto_option = ''
        if target_type == 'StaticLibrary':
            fat_lto_option = ';-ffat-lto-objects'
            message(
                context,
                'For unix added option -ffat-lto-objects to fix linking with -ipo.',
                ''
            )

        flag_values = {
            'ipoMultiFile': {ifort_cl_win: '-Qipo',
                             ifort_cl_unix: '-ipo{}'.format(fat_lto_option)},
            'ipoSingleFile': {ifort_cl_win: '-Qip',
                              ifort_cl_unix: '-ip'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_enable_enhanced_instruction_set(context, flag_name, flag_value):
        """
        Set EnableEnhancedInstructionSet

        """
        del context, flag_name, flag_value
        flag_values = {
            'codeArchSSE2': {ifort_cl_win: '-arch:SSE2',
                             ifort_cl_unix: '-arch SSE2'},
            'codeArchSSE3': {ifort_cl_win: '-arch:SSE3',
                             ifort_cl_unix: '-arch SSE3'},
            'codeArchAVX': {ifort_cl_win: '-arch:AVX',
                            ifort_cl_unix: '-arch AVX'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_enable_recursion(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-recursive',
                     ifort_cl_unix: '-recursive'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_reentrant_code(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'reentrancyNone': {ifort_cl_win: '-reentrancy:none',
                               ifort_cl_unix: '-reentrancy none'},
            'reentrancyAsync': {ifort_cl_win: '-reentrancy:async',
                                ifort_cl_unix: '-reentrancy async'},
            'reentrancyThreaded': {ifort_cl_win: '-reentrancy:threaded',
                                   ifort_cl_unix: '-reentrancy threaded'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_debug_information_format(context, flag_name, flag_value):
        """
        Set debug information format flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'debugEnabled': {ifort_cl_win: '-debug:full',
                             ifort_cl_unix: '-debug full'},
            'debugLineInfoOnly': {ifort_cl_win: '-debug:minimal',
                                  ifort_cl_unix: '-debug minimal'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_suppress_startup_banner(context, flag_name, flag_value):
        """
        Set suppress banner flag for compiler

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '-nologo'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_multi_processor_compilation(context, flag_name, flag_value):
        """
        Set MultiProcessorCompilation /MP

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_cl_win: '/MP',
                     ifort_cl_unix: '-multiple-processes'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_source_file_format(context, flag_name, flag_value):
        """
        Set source file format flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'fileFormatFree': {ifort_cl_win: '-free',
                               ifort_cl_unix: '-free'},
            'fileFormatFixed': {ifort_cl_win: '-fixed',
                                ifort_cl_unix: '-fixed'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_local_variable_storage(context, flag_name, flag_value):
        """
        Set local variable storage flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'localStorageAutomatic': {ifort_cl_win: '-Qauto',
                                      ifort_cl_unix: '-auto'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_real_kind(context, flag_name, flag_value):
        """
        Set real kind flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'realKIND8': {ifort_cl_win: '-real-size:64',
                          ifort_cl_unix: '-real-size 64'},
            'realKIND16': {ifort_cl_win: '-real-size:128',
                           ifort_cl_unix: '-real-size 128'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __get_no_prefix(unix_option):
        no = ''
        if unix_option[-1:] == '-':
            no = '-no'
        return no

    def __set_additional_options(self, context, flag_name, flag_value):
        """
        Set Additional options

        """
        # for setting in context.settings:
        add_opts = flag_value
        if add_opts:
            add_opts = set_unix_slash(add_opts).split()
            ready_add_opts = []
            for add_opt in add_opts:
                add_opt = add_opt.strip()
                if '/Qprof-dir' in add_opt:
                    name_value = add_opt.split(':')
                    prof_dir = normalize_path(
                        context,
                        os.path.dirname(context.vcxproj_path), name_value[1]
                    )
                    prof_dir = cleaning_output(context, prof_dir)
                    add_opt = name_value[0] + ':' + prof_dir

                add_opt = '-' + add_opt[1:]
                ready_add_opts.append(add_opt)
                unix_option = add_opt.replace(':', ' ')
                if 'gen-interfaces' in unix_option:
                    pass
                elif 'Qprec-div' in unix_option:
                    unix_option = FortranFlags.__get_no_prefix(unix_option) + '-prec-div'
                elif unix_option == '-static':
                    pass
                elif 'Qprof-dir' in unix_option:
                    unix_option = unix_option.replace('Qprof-dir', 'prof-dir')
                elif 'Qprof-gen' in unix_option:
                    unix_option = unix_option.replace('Qprof-gen', 'prof-gen')
                elif 'Qprof-use' in unix_option:
                    unix_option = unix_option.replace('Qprof-use', 'prof-use')
                elif 'Qprec-sqrt' in unix_option:
                    unix_option = FortranFlags.__get_no_prefix(unix_option) + '-prec-sqrt'
                elif 'Qopenmp-lib' in unix_option:
                    unix_option = unix_option.replace('Qopenmp-lib', 'qopenmp-lib')
                    unix_option = unix_option.replace('lib ', 'lib=')
                else:
                    message(context, 'Unix ifort option "{}" may be incorrect. '
                            'Check it and set it with visual studio UI if possible.'
                            .format(unix_option), 'warn')
                if ifort_cl_win not in self.flags[flag_name]:
                    self.flags[flag_name][ifort_cl_win] = []
                self.flags[flag_name][ifort_cl_win].append(add_opt)
                if ifort_cl_unix not in self.flags[flag_name]:
                    self.flags[flag_name][ifort_cl_unix] = []
                self.flags[flag_name][ifort_cl_unix].append(unix_option)
            message(context,
                    'Additional Options : {}'.format(str(ready_add_opts)), '')

    @staticmethod
    def __set_generate_manifest(context, flag_name, flag_value):
        """ Set GenerateManifest flag: /MANIFEST """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_ln_win: '/MANIFEST'},
            'false': {ifort_ln_win: '/MANIFEST:NO'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __generate_debug_information(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_ln_win: '/DEBUG'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __show_progress(context, flag_name, flag_value):
        del context, flag_name, flag_value
        flag_values = {
            'linkProgressLibs': {ifort_ln_win: '/VERBOSE:LIB'},
            'linkProgressAll': {ifort_ln_win: '/VERBOSE'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_link_incremental(context, flag_name, flag_value):
        """
        Set LinkIncremental flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'linkIncrementalYes': {ifort_ln_win: '/INCREMENTAL'},
            'linkIncrementalNo': {ifort_ln_win: '/INCREMENTAL:NO'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_link_suppress_startup_banner(context, flag_name, flag_value):
        """
        Set suppress banner flag for linker

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_ln_win: '/NOLOGO'},
            default_value: {}
        }
        return flag_values

    def __set_ignore_default_library_names(self, context, flag_name, flag_value):
        """
        Set IgnoreDefaultLibraryNames for linker

        """
        del flag_name
        ignore_libs = self.get_no_default_lib_link_flags(flag_value)
        if ignore_libs:
            context.settings[context.current_setting][ifort_ln_win] += ignore_libs
            message(context, 'Ignore Default Library Names : {}'.format(ignore_libs), '')

    @staticmethod
    def __set_optimize_references(context, flag_name, flag_value):
        """
        Set OptimizeReferences flag: /OPT:REF

        """
        del context, flag_name, flag_value
        flag_values = {
            'optReferences': {ifort_ln_win: '/OPT:REF'},
            'optNoReferences': {ifort_ln_win: '/OPT:NOREF'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_enable_comdat_folding(context, flag_name, flag_value):
        """
        Set EnableCOMDATFolding flag: /OPT:ICF

        """
        del context, flag_name, flag_value
        flag_values = {
            'optFolding': {ifort_ln_win: '/OPT:ICF'},
            'optNoFolding': {ifort_ln_win: '/OPT:NOICF'},
            default_value: {}
        }

        return flag_values

    @staticmethod
    def __set_target_machine(context, flag_name, flag_value):
        """
        Set TargetMachine flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'machineX86': {ifort_ln_win: '/MACHINE:IX86'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_sub_system(context, flag_name, flag_value):
        """
        Set SubSystem flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'subSystemWindows': {ifort_ln_win: '/SUBSYSTEM:WINDOWS'},
            'subSystemConsole': {ifort_ln_win: '/SUBSYSTEM:CONSOLE'},
            'subSystemConsoleXP': {ifort_ln_win: '/SUBSYSTEM:CONSOLE,"5.x"'},
            'subSystemWindowsXP': {ifort_ln_win: '/SUBSYSTEM:WINDOWS,"5.x"'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_link_dll(context, flag_name, flag_value):
        """
        Set LinkDLL flag

        """
        del context, flag_name, flag_value
        flag_values = {
            'true': {ifort_ln_win: '/DLL'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def __set_additional_link_options(context, flag_name, flag_value):
        """
        Set LinkDLL flag

        """
        del context, flag_name

        flag_values = {}
        if flag_value:
            flag_values.update(
                {
                    flag_value: {ifort_ln_win: flag_value},
                    default_value: {}
                }
            )
        return flag_values
