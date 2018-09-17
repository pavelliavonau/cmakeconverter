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

from cmake_converter.utils import message, write_comment, is_settings_has_data
from cmake_converter.utils import write_property_of_settings
from cmake_converter.utils import get_str_value_from_property_value

cl_flags = 'cl_flags'               # MSVC compile flags (Windows only)
ln_flags = 'ln_flags'               # MSVC link flags (Windows only)
ifort_cl_win = 'ifort_cl_win'       # ifort compile flags (Windows)
ifort_cl_unix = 'ifort_cl_unix'     # ifort compile flags (Unix)
ifort_ln = 'ifort_ln'               # ifort link flags
defines = 'defines'                 # compile definitions (cross platform)
default_value = 'default_value'

pch_macro_text = """MACRO(ADD_PRECOMPILED_HEADER PrecompiledHeader PrecompiledSource SourcesVar)
    if(MSVC)
        list(REMOVE_ITEM ${SourcesVar} ${PrecompiledSource})
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


class Flags:
    """
        Class who manage flags of projects
    """

    @staticmethod
    def __write_defines_for_flags(cmake_file, indent, config_condition_expr, property_value, width):
        del width
        config = config_condition_expr.replace('$<CONFIG:', '')
        config = config.replace('>', '')
        cmake_file.write(
            '{0}    COMPILE_DEFINITIONS_{1} "{2}"\n'
            .format(indent, config.upper(), get_str_value_from_property_value(property_value))
        )

    def write_defines(self, context, cmake_file):
        write_comment(cmake_file, 'Compile definitions')
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            'target_compile_definitions(${PROJECT_NAME} PRIVATE', ')', defines
        )
        for file in context.file_contexts:
            write_property_of_settings(
                cmake_file,
                context.file_contexts[file].settings,
                context.sln_configurations_map,
                'set_source_files_properties({0} PROPERTIES'.format(file),
                ')',
                defines,
                '',
                None,
                self.__write_defines_for_flags
            )
        cmake_file.write('\n')

    @staticmethod
    def __write_flags_of_files(cmake_file, indent, config_condition_expr, property_value, width):
        property_value_str = ' '.join(property_value)
        config_width = width + 3  # for '"$<'
        cmake_file.write('{0}    {1:>{width}}:{2}>"\n'
                         .format(indent, '"$<' + config_condition_expr, property_value_str,
                                 width=config_width))

    def write_compiler_and_linker_flags(self, context, os_check_str, compiler_check_str,
                                        compiler_flags_key, linker_flags_key, cmake_file):
        and_os_str = ''
        if os_check_str:
            and_os_str = ' AND {0}'.format(os_check_str)
        cmake_file.write('if({0}{1})\n'.format(compiler_check_str, and_os_str))
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            'target_compile_options(${PROJECT_NAME} PRIVATE', ')', compiler_flags_key, indent='    '
        )
        for file in context.file_contexts:
            file_cl_var = 'FILE_CL_OPTIONS'
            text = write_property_of_settings(
                cmake_file, context.file_contexts[file].settings,
                context.sln_configurations_map,
                'string(CONCAT {0}'.format(file_cl_var),
                ')', compiler_flags_key, '    ', None, self.__write_flags_of_files
            )
            if text:
                cmake_file.write(
                    '    set_source_files_properties({0} PROPERTIES COMPILE_FLAGS ${{{1}}})\n'
                    .format(file, file_cl_var))

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
    def write_target_headers_only_artifact(context, cmake_file):
        """
        Add a dummy target to given CMake file

        :param context: the context of converter
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        message(context, 'CMake will show fake custom Library.', 'warn')
        cmake_file.write('add_custom_target(${PROJECT_NAME} SOURCES ${ALL_FILES})\n\n')

    def write_precompiled_headers_macro(self, context, cmake_file):
        pass

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
