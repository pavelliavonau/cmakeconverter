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

"""
    Flags
    =====
     Manage compilation flags of project
"""

from collections import OrderedDict

from cmake_converter.utils import message, write_comment, is_settings_has_data
from cmake_converter.utils import write_property_of_settings

cl_flags = 'cl_flags'               # MSVC compile flags (Windows only)
ln_flags = 'ln_flags'               # MSVC link flags (Windows only)
ifort_cl_win = 'ifort_cl_win'       # ifort compile flags (Windows)
ifort_cl_unix = 'ifort_cl_unix'     # ifort compile flags (Unix)
ifort_ln = 'ifort_ln'               # ifort link flags
defines = 'defines'                 # compile definitions (cross platform)
default_value = 'default_value'


class Flags:
    """
        Class who manage flags of projects
    """

    @staticmethod
    def __write_defines_for_files(cmake_file,
                                  indent,
                                  config_condition_expr,
                                  property_value,
                                  width,
                                  **kwargs):
        del width
        config = config_condition_expr.replace('$<CONFIG:', '')
        config = config.replace('>', '')
        cmake_file.write(
            '{0}    COMPILE_DEFINITIONS_{1} "{2}"\n'
            .format(indent, config.upper(), ';'.join(property_value))
        )

    def write_defines(self, context, cmake_file):
        write_comment(cmake_file, 'Compile definitions')
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            begin_text='target_compile_definitions(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=defines,
            separator=';\n',
            in_quotes=True
        )
        for file in context.file_contexts:
            write_property_of_settings(
                cmake_file,
                context.file_contexts[file].settings,
                context.sln_configurations_map,
                begin_text='set_source_files_properties({0} PROPERTIES'.format(file),
                end_text=')',
                property_name=defines,
                write_setting_property_func=self.__write_defines_for_files
            )
        cmake_file.write('\n')

    @staticmethod
    def __write_compile_flags(context, cmake_file, compiler_flags_key):
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            begin_text='target_compile_options(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=compiler_flags_key,
            indent='    ',
            ignore_global=True  # TODO: get rid of global defaults and make False
        )
        for file in context.file_contexts:
            file_cl_var = 'FILE_CL_OPTIONS'
            text = write_property_of_settings(
                cmake_file, context.file_contexts[file].settings,
                context.sln_configurations_map,
                begin_text='string(CONCAT {0}'.format(file_cl_var),
                end_text=')',
                property_name=compiler_flags_key,
                indent='    ',
                in_quotes=True
            )
            if text:
                cmake_file.write(
                    '    source_file_compile_options({0} ${{{1}}})\n'
                    .format(file, file_cl_var))

    @staticmethod
    def __write_link_flags(context, cmake_file, settings_of_arch, linker_flags_key):
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
                    configuration_type = context.settings[mapped_setting_name]['target_type']
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
            and_os_str = ' AND {0}'.format(os_check_str)
        cmake_file.write('if({0}{1})\n'.format(compiler_check_str, and_os_str))

        Flags.__write_compile_flags(context, cmake_file, compiler_flags_key)

        settings_of_arch = OrderedDict()
        for sln_setting in context.sln_configurations_map:
            if sln_setting is None:
                continue
            arch = sln_setting.split('|')[1]
            if arch not in settings_of_arch:
                settings_of_arch[arch] = OrderedDict()
            settings_of_arch[arch][sln_setting] = sln_setting

        Flags.__write_link_flags(context, cmake_file, settings_of_arch, linker_flags_key)

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
                linker_flags_key=ifort_ln
            )
            self.write_compile_and_link_flags(
                context, cmake_file,
                os_check_str='UNIX',
                compiler_check_str='${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel"',
                compiler_flags_key=ifort_cl_unix,
                linker_flags_key=ifort_ln
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

    def write_use_pch_macro(self, context, cmake_file):
        pass

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
            if s is None:
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
