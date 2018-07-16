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
                message(context, '{0} for {1} is {2} '.format(attr, setting, flags_message), '')

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
        self.set_floating_point_stack_check(context)
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

    def set_floating_point_stack_check(self, context):
        flag_values = {
            'true': {ifort_cl_win: '-Qfp-stack-check',
                     ifort_cl_unix: '-fp-stack-check'},
            'false': {},
            default_value: {}
        }
        self.set_flag(context, 'VFFortranCompilerTool', 'FloatingPointStackCheck', flag_values)

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
    def __get_no_prefix(unix_option):
        no = ''
        if unix_option[-1:] == '-':
            no = '-no'
        return no

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
                    context.settings[setting][ifort_cl_win].append(add_opt)
                    context.settings[setting][ifort_cl_unix].append(unix_option)
                message(context,
                        'Additional Options for {0} : {1}'.format(setting, str(ready_add_opts)), '')
            else:
                message(context, 'No Additional Options for {0}'.format(setting), '')
