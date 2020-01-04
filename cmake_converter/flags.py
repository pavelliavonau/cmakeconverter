#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019:
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
    Flags
    =====
     Manage compilation flags of project
"""

from cmake_converter.utils import message, write_comment
from cmake_converter.utils import write_property_of_settings

cl_flags = 'cl_flags'               # MSVC compile flags (Windows only)
ln_flags = 'ln_flags'               # MSVC link flags (Windows only)
ifort_cl_win = 'ifort_cl_win'       # ifort compile flags (Windows)
ifort_cl_unix = 'ifort_cl_unix'     # ifort compile flags (Unix)
ifort_ln_win = 'ifort_ln_win'       # ifort link flags for windows
ifort_ln_unix = 'ifort_ln_unix'     # ifort link flags for unix
defines = 'defines'                 # compile definitions (cross platform)
default_value = 'default_value'


class Flags:
    """
        Class who manage flags of projects
    """

    @staticmethod
    def get_no_default_lib_link_flags(flag_value):
        """Helper to get list of /NODEFAULTLIB flags"""
        if flag_value != '':
            ignore_libs = []
            for spec_lib in flag_value.split(';'):
                spec_lib = spec_lib.strip()
                if spec_lib:
                    ignore_libs.append('/NODEFAULTLIB:' + spec_lib)
            return ignore_libs

    @staticmethod
    def __write_defines_for_files(cmake_file,
                                  property_indent,
                                  config_condition_expr,
                                  property_value,
                                  width,
                                  **kwargs):
        del width
        config = ''
        if config_condition_expr:
            config = config_condition_expr.replace('$<CONFIG:', '_')
            config = config.replace('>', '')

        cmake_file.write(
            '{}{}COMPILE_DEFINITIONS{} "{}"\n'
            .format(property_indent, kwargs['main_indent'],
                    config.upper(), ';'.join(property_value))
        )

    def write_defines(self, context, cmake_file):
        """ Routine that writes compile definitions into CMake file """
        write_comment(cmake_file, 'Compile definitions')
        write_property_of_settings(
            context, cmake_file,
            begin_text='target_compile_definitions(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=defines,
            separator=';\n',
            in_quotes=True
        )
        for file in context.file_contexts:
            write_property_of_settings(
                context.file_contexts[file],
                cmake_file,
                begin_text='set_source_files_properties({} PROPERTIES'.format(file),
                end_text=')',
                property_name=defines,
                write_setting_property_func=self.__write_defines_for_files
            )
        cmake_file.write('\n')

    @staticmethod
    def __write_compile_flags(context, cmake_file, compiler_flags_key):
        write_property_of_settings(
            context, cmake_file,
            begin_text='target_compile_options(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=compiler_flags_key,
            separator=';\n',
            indent=context.indent
        )
        for file in context.file_contexts:
            file_cl_var = 'FILE_CL_OPTIONS'
            text = write_property_of_settings(
                context.file_contexts[file], cmake_file,
                begin_text='string(CONCAT {}'.format(file_cl_var),
                end_text=')',
                property_name=compiler_flags_key,
                indent=context.indent,
                in_quotes=True
            )
            if text:
                cmake_file.write(
                    '{}source_file_compile_options({} ${{{}}})\n'
                    .format(context.indent, file, file_cl_var))

    @staticmethod
    def __write_link_flags(context, cmake_file, linker_flags_key):
        write_property_of_settings(
            context, cmake_file,
            begin_text='target_link_options(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=linker_flags_key,
            separator=';\n',
            indent=context.indent
        )

    @staticmethod
    def write_compile_and_link_flags(context, cmake_file, **kwargs):
        """

        :param context:
        :param cmake_file:
        :param kwargs:
        :return:
        """
        os_check_str = kwargs['os_check_str']
        compiler_check_str = kwargs['compiler_check_str']
        compiler_flags_key = kwargs['compiler_flags_key']
        linker_flags_key = kwargs['linker_flags_key']

        and_os_str = ''
        if os_check_str:
            and_os_str = ' AND {}'.format(os_check_str)
        cmake_file.write('if({}{})\n'.format(compiler_check_str, and_os_str))

        Flags.__write_compile_flags(context, cmake_file, compiler_flags_key)
        Flags.__write_link_flags(context, cmake_file, linker_flags_key)

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
            self.write_compile_and_link_flags(
                context, cmake_file,
                os_check_str=None,
                compiler_check_str='MSVC',
                compiler_flags_key=cl_flags,
                linker_flags_key=ln_flags,
            )

        if is_ifort:
            self.write_compile_and_link_flags(
                context, cmake_file,
                os_check_str='WIN32',
                compiler_check_str='${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"',
                compiler_flags_key=ifort_cl_win,
                linker_flags_key=ifort_ln_win
            )
            self.write_compile_and_link_flags(
                context, cmake_file,
                os_check_str='UNIX',
                compiler_check_str='${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"',
                compiler_flags_key=ifort_cl_unix,
                linker_flags_key=ifort_ln_unix
            )

    @staticmethod
    def write_target_headers_only_artifact(context, cmake_file):
        """
        Add a dummy target to given CMake file

        :param context: the context of converter
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message(context, 'CMake will show fake custom Library.', '')
        cmake_file.write('add_custom_target(${PROJECT_NAME} SOURCES ${ALL_FILES})\n\n')

    def write_use_pch_function(self, context, cmake_file):
        """ Dummy to fix crash """

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
            if None in s:
                continue
            configuration_type = context.settings[s]['target_type']
            if configuration_type:
                break
        if configuration_type:
            if configuration_type == 'DynamicLibrary':
                cmake_file.write('add_library(${PROJECT_NAME} SHARED')
                message(context, 'CMake will build a SHARED Library.', '')
            elif configuration_type == 'StaticLibrary':  # pragma: no cover
                cmake_file.write('add_library(${PROJECT_NAME} STATIC')
                message(context, 'CMake will build a STATIC Library.', '')
            else:  # pragma: no cover
                cmake_file.write('add_executable(${PROJECT_NAME}')
                message(context, 'CMake will build an EXECUTABLE.', '')
            cmake_file.write(' ${ALL_FILES})\n')

        if context.solution_folder:
            cmake_file.write(
                'set_target_properties(${{PROJECT_NAME}} PROPERTIES FOLDER "{}")\n'.format(
                    context.solution_folder
                )
            )

        cmake_file.write('\n')
