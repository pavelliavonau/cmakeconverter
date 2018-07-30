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

import os

from cmake_converter.flags import *
from cmake_converter.utils import normalize_path
from cmake_converter.utils import set_unix_slash


class FortranFlags(Flags):
    """
        Class who check and create compilation flags for Fortran compiler
    """

    def __init__(self):
        self.flags = {}
        self.flags_handlers = {
            'SuppressStartupBanner': self.set_suppress_startup_banner,
            'DebugInformationFormat': self.set_debug_information_format,
            'Optimization': self.set_optimization,
            'Preprocess': self.set_preprocess_source_file,
            'SourceFileFormat': self.set_source_file_format,
            'DebugParameter': self.set_debug_parameter,
            'DefaultIncAndUsePath': self.set_default_inc_and_use_path,
            'FixedFormLineLength': self.set_fixed_form_line_length,
            'OpenMP': self.set_open_mp,
            'DisableSpecificDiagnostics': self.set_disable_specific_diagnostics,
            'Diagnostics': self.set_diagnostics,
            'WarnDeclarations': self.set_warn_declarations,
            'WarnUnusedVariables': self.set_warn_unused_variables,
            'WarnIgnoreLOC': self.set_warn_ignore_loc,
            'WarnTruncateSource': self.set_warn_truncate_source,
            'WarnInterfaces': self.set_warn_interfaces,
            'WarnUnalignedData': self.set_warn_unaligned_data,
            'WarnUncalled': self.set_warn_uncalled,
            'SuppressUsageMessages': self.set_suppress_usage_messages,
            'RealKIND': self.set_real_kind,
            'LocalVariableStorage': self.set_local_variable_storage,
            'InitLocalVarToNAN': self.set_init_local_var_to_nan,
            'FloatingPointExceptionHandling': self.set_floating_point_exception_handling,
            'ExtendSinglePrecisionConstants': self.set_extend_single_precision_constants,
            'FloatingPointStackCheck': self.set_floating_point_stack_check,
            'ExternalNameInterpretation': self.set_external_name_interpretation,
            'StringLengthArgPassing': self.set_string_length_arg_passing,
            'ExternalNameUnderscore': self.set_external_name_underscore,
            'Traceback': self.set_traceback,
            'RuntimeChecks': self.set_runtime_checks,
            'ArgTempCreatedCheck': self.set_arg_temp_created_check,
            'RuntimeLibrary': self.set_runtime_library,
            'DisableDefaultLibSearch': self.set_disable_default_lib_search,
            'AdditionalOptions': self.set_additional_options,
        }

    def __set_default_flags(self, context):
        for flag_name in self.__get_result_order_of_flags():
            self.flags[flag_name] = {}
            self.set_flag(context, flag_name, '', None)

    @staticmethod
    def __get_result_order_of_flags():
        flags_list = [
            'SuppressStartupBanner',
            'DebugInformationFormat',
            'Optimization',
            'Preprocess',
            'SourceFileFormat',
            'DebugParameter',
            'DefaultIncAndUsePath',
            'FixedFormLineLength',
            'OpenMP',
            'DisableSpecificDiagnostics',
            'Diagnostics',
            'WarnDeclarations',
            'WarnUnusedVariables',
            'WarnIgnoreLOC',
            'WarnTruncateSource',
            'WarnInterfaces',
            'WarnUnalignedData',
            'WarnUncalled',
            'SuppressUsageMessages',
            'RealKIND',
            'LocalVariableStorage',
            'InitLocalVarToNAN',
            'FloatingPointExceptionHandling',
            'ExtendSinglePrecisionConstants',
            'FloatingPointStackCheck',
            'ExternalNameInterpretation',
            'StringLengthArgPassing',
            'ExternalNameUnderscore',
            'Traceback',
            'RuntimeChecks',
            'ArgTempCreatedCheck',
            'RuntimeLibrary',
            'DisableDefaultLibSearch',
            'AdditionalOptions',
        ]
        return flags_list

    def set_flag(self, context, flag_name, flag_value, node):
        """
        Set flag helper

        :param context: converter Context
        :type context: Context
        :param flag_name:
        :param flag_value:
        :return:
        """

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
            for key in values:
                value = values[key]
                self.flags[flag_name][key] = [value]
                flags_message[key] = value

        if flags_message:
            message(
                context,
                '{0} is {1} '.format(flag_name, flags_message),
                ''
            )

    def prepare_context_for_flags(self, context):
        context.settings[context.current_setting][ifort_cl_win] = []
        context.settings[context.current_setting][ifort_cl_unix] = []
        context.settings[context.current_setting][ifort_ln] = []
        context.settings[context.current_setting]['assume_args'] = []
        self.__set_default_flags(context)

    def apply_flags_to_context(self, context):
        context_flags_data_keys = [
            ifort_cl_win,
            ifort_cl_unix,
            ifort_ln,
            'assume_args',
        ]

        for flag_name in self.__get_result_order_of_flags():
            for context_flags_data_key in context_flags_data_keys:
                if context_flags_data_key in self.flags[flag_name]:
                    for value in self.flags[flag_name][context_flags_data_key]:
                        context.settings[context.current_setting][context_flags_data_key].append(
                            value
                        )

        self.__set_assume_with_params(context)

    @staticmethod
    def __set_assume_with_params(context):
        if 'assume_args' in context.settings[context.current_setting]:
            args = context.settings[context.current_setting]['assume_args']
            context.settings[context.current_setting][ifort_cl_win].append('-assume:' + ','.join(args))
            context.settings[context.current_setting][ifort_cl_unix].append('-assume ' + ','.join(args))

    def set_floating_point_stack_check(self, context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-Qfp-stack-check',
                     ifort_cl_unix: '-fp-stack-check'},
            'false': {},
            default_value: {}
        }
        return flag_values

    def set_external_name_underscore(self, context, flag_name, flag_value):
        flag_values = {
            'true': {'assume_args': 'underscore'},
            'false': {'assume_args': 'nounderscore'},
            default_value: {'assume_args': 'nounderscore'}
        }
        return flag_values

    def set_external_name_interpretation(self, context, flag_name, flag_value):
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
        return flag_values

    def set_diagnostics(self, context, flag_name, flag_value):
        flag_values = {
            'diagnosticsShowAll': {ifort_cl_win: '-warn:all',
                                   ifort_cl_unix: '-warn all'},
            'diagnosticsDisableAll': {ifort_cl_win: '-warn:none',
                                      ifort_cl_unix: '-warn none'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_declarations(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:declaration',
                     ifort_cl_unix: '-warn declaration'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_unused_variables(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:unused',
                     ifort_cl_unix: '-warn unused'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_ignore_loc(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:ignore_loc',
                     ifort_cl_unix: '-warn ignore_loc'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_truncate_source(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:truncated_source',
                     ifort_cl_unix: '-warn truncated_source'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_interfaces(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:interfaces',
                     ifort_cl_unix: '-warn interfaces'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_unaligned_data(context, flag_name, flag_value):
        flag_values = {
            'false': {ifort_cl_win: '-warn:noalignments',
                      ifort_cl_unix: '-warn noalignments'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_warn_uncalled(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:uncalled',
                     ifort_cl_unix: '-warn uncalled'},
            default_value: {}
        }
        return flag_values

    @staticmethod
    def set_suppress_usage_messages(context, flag_name, flag_value):
        flag_values = {
            'true': {ifort_cl_win: '-warn:nousage',
                     ifort_cl_unix: '-warn nousage'},
            default_value: {}
        }
        return flag_values

    def set_arg_temp_created_check(self, context, flag_name, flag_value):
        """
        """
        flag_values = {
            'true': {ifort_cl_win: '-check:arg_temp_created',
                     ifort_cl_unix: '-check arg_temp_created'},
            default_value: {}
        }
        return flag_values

    def set_debug_parameter(self, context, flag_name, flag_value):
        """
        """
        flag_values = {
            'debugParameterAll': {ifort_cl_win: '-debug-parameters:all',
                                  ifort_cl_unix: '-debug-parameters all'},
            'debugParameterUsed': {ifort_cl_win: '-debug-parameters:used',
                                   ifort_cl_unix: '-debug-parameters used'},
            default_value: {}
        }
        return flag_values

    def set_fixed_form_line_length(self, context, flag_name, flag_value):
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
        return flag_values

    def set_default_inc_and_use_path(self, context, flag_name, flag_value):
        """
        Set default include and path

        """

        flag_values = {
            'defaultIncludeCurrent': {'assume_args': 'nosource_include'},
            default_value: {'assume_args': 'source_include'}
        }
        return flag_values

    def set_open_mp(self, context, flag_name, flag_value):
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
        return flag_values

    def set_disable_specific_diagnostics(self, context, flag_name, flag_value):
        """
        Set disable specific diagnostic flag

        """

        # TODO: split list
        opt = flag_value
        if opt:
            self.flags[flag_name][ifort_cl_win] = ['-Qdiag-disable:{0}'.format(opt)]
            self.flags[flag_name][ifort_cl_unix] = ['-diag-disable={0}'.format(opt)]

    def set_string_length_arg_passing(self, context, flag_name, flag_value):
        """
        Set string lengh arg parsing

        """
        flag_values = {
            'strLenArgsMixed': {ifort_cl_win: '-iface:mixed_str_len_arg'},
            default_value: {}
        }
        return flag_values

    def set_runtime_library(self, context, flag_name, flag_value):
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
        return flag_values

    def set_disable_default_lib_search(self, context, flag_name, flag_value):
        """
        Set disable default lib search

        """
        flag_values = {
            'true': {ifort_cl_win: '-libdir:noauto'},
            default_value: {}
        }
        return flag_values

    def set_runtime_checks(self, context, flag_name, flag_value):
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
        return flag_values

    def set_traceback(self, context, flag_name, flag_value):
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
        return flag_values

    def set_extend_single_precision_constants(self, context, flag_name, flag_value):
        """
        Set extend single precision constants flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-fpconstant',
                     ifort_cl_unix: '-fpconstant'},
            default_value: {}
        }
        return flag_values

    def set_floating_point_exception_handling(self, context, flag_name, flag_value):
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
        return flag_values

    def set_init_local_var_to_nan(self, context, flag_name, flag_value):
        """
        Set init local var to NaN flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-Qtrapuv',
                     ifort_cl_unix: '-ftrapuv'},
            default_value: {}
        }
        return flag_values

    def set_preprocess_source_file(self, context, flag_name, flag_value):
        """
        Set preprocess source file flag

        """
        flag_values = {
            'preprocessYes': {ifort_cl_win: '-fpp',
                              ifort_cl_unix: '-fpp'},
            default_value: {}
        }
        return flag_values

    def set_optimization(self, context, flag_name, flag_value):
        """
        Set optimization flag

        """
        flag_values = {
            'optimizeMinSpace': {ifort_cl_win: '-O1',
                                 ifort_cl_unix: '-O1'},
            'optimizeFull': {ifort_cl_win: '-O3',
                             ifort_cl_unix: '-O3'},
            'optimizeDisabled': {ifort_cl_win: '-Od',
                                 ifort_cl_unix: '-Od'},
            default_value: {ifort_cl_win: '-O2',
                            ifort_cl_unix: '-O2'}
        }
        return flag_values

    def set_debug_information_format(self, context, flag_name, flag_value):
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
        return flag_values

    def set_suppress_startup_banner(self, context, flag_name, flag_value):
        """
        Set supress banner flag

        """
        flag_values = {
            'true': {ifort_cl_win: '-nologo'},
            default_value: {}
        }
        return flag_values

    def set_source_file_format(self, context, flag_name, flag_value):
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
        return flag_values

    def set_local_variable_storage(self, context, flag_name, flag_value):
        """
        Set local variable storage flag

        """
        flag_values = {
            'localStorageAutomatic': {ifort_cl_win: '-Qauto',
                                      ifort_cl_unix: '-auto'},
            default_value: {}
        }
        return flag_values

    def set_real_kind(self, context, flag_name, flag_value):
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
        return flag_values

    @staticmethod
    def __get_no_prefix(unix_option):
        no = ''
        if unix_option[-1:] == '-':
            no = '-no'
        return no

    def set_additional_options(self, context, flag_name, flag_value):
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
                    add_opt = name_value[0] + ':' + normalize_path(
                        context,
                        os.path.dirname(context.vcxproj_path), name_value[1]
                    )

                add_opt = '-' + add_opt[1:]
                ready_add_opts.append(add_opt)
                unix_option = add_opt.replace(':', ' ')
                if 'gen-interfaces' in unix_option:
                    pass
                elif 'Qprec-div' in unix_option:
                    unix_option = FortranFlags.__get_no_prefix(unix_option) + '-prec-div'
                elif '-static' == unix_option:
                    pass
                elif 'Qprof-dir' in unix_option:
                    unix_option = unix_option.replace('Qprof-dir', 'prof-dir')
                elif 'Qprof-use' in unix_option:
                    unix_option = unix_option.replace('Qprof-use', 'prof-use')
                elif 'Qprec-sqrt' in unix_option:
                    unix_option = FortranFlags.__get_no_prefix(unix_option) + '-prec-sqrt'
                elif 'Qopenmp-lib' in unix_option:
                    unix_option = unix_option.replace('Qopenmp-lib', 'openmp-lib')
                    unix_option = unix_option.replace('lib ', 'lib=')
                else:
                    message(context, 'Unix ifort option "{0}" may be incorrect. '
                            'Check it and set it with visual studio UI if possible.'
                            .format(unix_option), 'warn')
                if ifort_cl_win not in self.flags[flag_name]:
                    self.flags[flag_name][ifort_cl_win] = []
                self.flags[flag_name][ifort_cl_win].append(add_opt)
                if ifort_cl_unix not in self.flags[flag_name]:
                    self.flags[flag_name][ifort_cl_unix] = []
                self.flags[flag_name][ifort_cl_unix].append(unix_option)
            message(context,
                    'Additional Options : {0}'.format(str(ready_add_opts)), '')
