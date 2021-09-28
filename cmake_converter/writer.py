#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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
    CMakeWriter
    =============
     Writes formatted data to cmake scripts
"""

import os
from collections import OrderedDict

from cmake_converter.utils import message, make_cmake_literal,\
    normalize_path, is_settings_has_data, set_unix_slash
from cmake_converter.flags import defines, cl_flags, ln_flags, ifort_cl_win, ifort_cl_unix,\
    ifort_ln_win, ifort_ln_unix
from cmake_converter.data_files import get_cmake_lists

# pylint: disable=R0904


class CMakeWriter:
    """
        Class that writes CMakeLists.txt for target and project
    """

    def write_target_cmake_lists(self, context, cmake_file):
        """ Writes CMakeLists.txt for parsed target """
        self.write_cmake_project(context, cmake_file)

        # Add additional code or not
        if context.additional_code is not None:
            self.add_additional_code(context, context.additional_code, cmake_file)

        self.write_source_groups(context, cmake_file)

        if context.sources:
            self.write_comment(cmake_file, 'Target')
            self.write_target_artifact(context, cmake_file)
            self.write_use_pch_function(context, cmake_file)
            self.write_target_property_sheets(context, cmake_file)
            self.write_target_outputs(context, cmake_file)
            self.write_include_directories(context, cmake_file)
            self.write_defines(context, cmake_file)
            self.write_flags(context, cmake_file)
            self.write_target_build_events(context, cmake_file)
            if (context.target_references
                    or context.add_lib_deps
                    or context.sln_deps
                    or context.packages):
                self.write_comment(cmake_file, 'Dependencies')
            self.write_sln_dependencies(context, cmake_file)
            self.write_link_dependencies(context, cmake_file)
            self.write_target_dependency_packages(context, cmake_file)
        else:
            self.write_target_headers_only_artifact(context, cmake_file)

    @staticmethod
    def write_cmake_project(context, cmake_file):
        """
        Write cmake project for given CMake file

        :param context: Converter context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if context.project_name == '':
            message(
                context,
                'No PROJECT NAME found or define. '
                'Check it!!',
                'error'
            )
        cmake_file.write(
            'set(PROJECT_NAME {})\n\n'.format(make_cmake_literal(context, context.project_name))
        )

    @staticmethod
    def add_additional_code(context, file_to_add, cmake_file):
        """
        Add additional file with CMake code inside

        :param context: the context of converter
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        :param file_to_add: the file who contains CMake code
        :type file_to_add: str
        """

        if file_to_add != '':
            try:
                with open(file_to_add, encoding='utf-8') as fc:
                    CMakeWriter.write_comment(cmake_file, 'Provides from external file.')
                    for line in fc:
                        cmake_file.write(line)
                cmake_file.write('\n')
                message(context, 'File of Code is added = ' + file_to_add, 'warn')
            except OSError as e:
                message(context, str(e), 'error')
                message(
                    context,
                    'Wrong data file ! Code was not added, please verify file name or path !',
                    'error'
                )

    @staticmethod
    def get_source_group_var(context, source_group_name):
        """ Evaluates variable from source group name """
        if not source_group_name:
            return 'no_group_source_files'

        source_group_name = source_group_name.replace(' ', '_')
        return make_cmake_literal(context, source_group_name.replace('\\\\', '__'))

    def write_source_groups(self, context, cmake_file):
        """ Writes source groups of project files into CMakwLists.txt """
        CMakeWriter.write_comment(cmake_file, 'Source groups')

        source_group_list = sorted(context.source_groups)
        for source_group in source_group_list:
            source_group_var = self.get_source_group_var(context, source_group)
            cmake_file.write('set({}\n'.format(source_group_var))
            for src_file in context.source_groups[source_group]:
                fmt = '{}"{}"\n'
                if context.file_contexts[src_file].excluded_from_build:
                    fmt = '#' + fmt
                    message(
                        context,
                        "file {} is excluded from build. Written but commented. "
                        "No support in CMake yet.".format(src_file),
                        'warn4'
                    )
                cmake_file.write(fmt.format(context.indent, src_file))

            cmake_file.write(')\n')
            cmake_file.write(
                'source_group("{}" FILES ${{{}}})\n\n'.format(source_group, source_group_var)
            )

        cmake_file.write('set(ALL_FILES\n')
        for source_group in source_group_list:
            cmake_file.write(
                '{}${{{}}}\n'.format(
                    context.indent,
                    self.get_source_group_var(context, source_group)
                )
            )
        cmake_file.write(')\n\n')

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

        if context.project_folder:
            cmake_file.write(
                'set_target_properties(${{PROJECT_NAME}} PROPERTIES FOLDER "{}")\n'.format(
                    context.project_folder
                )
            )

        cmake_file.write('\n')

    def write_use_pch_function(self, context, cmake_file):
        """ Writes using of PCH if needed """
        need_pch = False
        any_setting = None
        for setting in context.settings:
            if self.__setting_has_pch(context, setting):
                need_pch = True
                any_setting = setting
                break

        if need_pch:
            self.write_precompiled_headers(context, any_setting, cmake_file)

    @staticmethod
    def __setting_has_pch(context, setting):
        """
        Return if there is precompiled header or not for given setting

        :param context: converter Context
        :type context: Context
        :param setting: related setting (Release|x64, Debug|Win32,...)
        :type setting: str
        :return: if use PCH or not
        :rtype: bool
        """

        if 'PrecompiledHeader' not in context.settings[setting]:
            return False

        has_pch = context.settings[setting]['PrecompiledHeader']

        return 'Use' in has_pch

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
        working_path = os.path.dirname(context.vcxproj_path)
        cmake_file.write(
            'target_precompile_headers(${{PROJECT_NAME}} PRIVATE\n'
            '{}"$<$<COMPILE_LANGUAGE:CXX>:${{CMAKE_CURRENT_SOURCE_DIR}}/{}>"\n'
            ')\n\n'.format(
                context.indent,
                normalize_path(context, working_path, pch_header, False)
            )
        )

    @staticmethod
    def write_property_sheets(cmake_file, property_indent, config_condition_expr,
                              property_value, width, **kwargs):
        """ Write property sheets functor (helper) """
        del kwargs
        config = '"${CMAKE_CONFIGURATION_TYPES}" '
        width_diff = 0
        if config_condition_expr is not None:
            config = config_condition_expr.replace('$<CONFIG:', '').replace('>', '')
            config += ' '
            width_diff = len('$<CONFIG:>') - 1

        if property_value:
            for property_sheet_cmake in property_value:
                result_width = width - width_diff
                result_width = max(result_width, 0)
                cmake_file.write(
                    '{}use_props(${{PROJECT_NAME}} {:<{width}}"{}")\n'.format(
                        property_indent,
                        config,
                        property_sheet_cmake,
                        width=result_width)
                )

    @staticmethod
    def write_target_property_sheets(context, cmake_file):
        """
        Write target property sheets of current context

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if context.default_property_sheet:
            cmake_file.write(
                'use_props(${{PROJECT_NAME}} "${{CMAKE_CONFIGURATION_TYPES}}" "${{{}}}")\n'
                .format(context.default_property_sheet)
            )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'property_sheets'):
            CMakeWriter.write_comment(cmake_file, 'Includes for CMake from *.props')
            CMakeWriter.write_property_of_settings(
                context, cmake_file,
                begin_text='',
                end_text='',
                property_name='property_sheets',
                write_setting_property_func=CMakeWriter.write_property_sheets
            )
            cmake_file.write('\n')

    @staticmethod
    def write_target_property(cmake_file,
                              property_indent,
                              config_condition_expr,
                              property_value,
                              width,
                              **kwargs):
        """ Method for writing CMake target property """
        property_name = kwargs['property_name']

        config = ''
        if config_condition_expr is not None:
            config = '_' + config_condition_expr.replace('$<CONFIG:', '').replace('>', '')
        width_diff = len('$<CONFIG:>') - len('_')

        if property_value:
            for property_sheet_cmake in property_value:
                result_width = width - width_diff
                result_width = max(result_width, 0)
                cmake_file.write(
                    '{}{}{}{:<{width}} "{}"\n'.format(
                        property_indent,
                        kwargs['main_indent'],
                        property_name,
                        config.upper(),
                        property_sheet_cmake,
                        width=result_width)
                )

    @staticmethod
    def write_target_outputs(context, cmake_file):
        """
        Add outputs for each artefacts CMake target

        :param context: related full context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if not context.settings:
            return

        if context.root_namespace:
            cmake_file.write('set(ROOT_NAMESPACE {})\n\n'.format(context.root_namespace))

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='VS_GLOBAL_KEYWORD',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='COMMON_LANGUAGE_RUNTIME',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'TARGET_NAME'):
            CMakeWriter.write_comment(cmake_file, 'Target name')
            CMakeWriter.write_property_of_settings(
                context,
                cmake_file,
                begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
                end_text=')',
                property_name='TARGET_NAME',
                write_setting_property_func=CMakeWriter.write_target_property
            )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'OUTPUT_DIRECTORY'):
            CMakeWriter.write_comment(cmake_file, 'Output directory')
            CMakeWriter.write_property_of_settings(
                context,
                cmake_file,
                begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
                end_text=')',
                property_name='OUTPUT_DIRECTORY',
                write_setting_property_func=CMakeWriter.write_target_property
            )

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='ARCHIVE_OUTPUT_DIRECTORY',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='ARCHIVE_OUTPUT_NAME',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='PDB_OUTPUT_DIRECTORY',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        # PDB_NAME doesn't support generator expressions yet (CMake 3.13)
        # CMakeWriter.write_property_of_settings(
        #     context,
        #     cmake_file,
        #     begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
        #     end_text=')',
        #     property_name='PDB_NAME',
        #     write_setting_property_func=ProjectVariables.write_target_property
        # )

        CMakeWriter.write_property_of_settings(
            context,
            cmake_file,
            begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
            end_text=')',
            property_name='INTERPROCEDURAL_OPTIMIZATION',
            write_setting_property_func=CMakeWriter.write_target_property
        )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'MSVC_RUNTIME_LIBRARY'):
            CMakeWriter.write_comment(cmake_file, 'MSVC runtime library')
            cmake_file.write('get_property(MSVC_RUNTIME_LIBRARY_DEFAULT TARGET ${PROJECT_NAME} '
                             'PROPERTY MSVC_RUNTIME_LIBRARY)\n')
            CMakeWriter.write_property_of_settings(
                context,
                cmake_file,
                begin_text='string(CONCAT "MSVC_RUNTIME_LIBRARY_STR"',
                end_text=')',
                property_name='MSVC_RUNTIME_LIBRARY',
                default='${MSVC_RUNTIME_LIBRARY_DEFAULT}'
            )
            cmake_file.write('set_target_properties(${PROJECT_NAME} PROPERTIES MSVC_RUNTIME_LIBRARY'
                             ' ${MSVC_RUNTIME_LIBRARY_STR})\n\n')

        # No support of Regex for Fortran_MODULE_DIRECTORY at CMake 3.13
        # CMakeWriter.write_property_of_settings(
        #     cmake_file, context.settings,
        #     context.sln_configurations_map,
        #     begin_text='set_target_properties(${PROJECT_NAME} PROPERTIES',
        #     end_text=')',
        #     property_name='Fortran_MODULE_DIRECTORY',
        #     write_setting_property_func=ProjectVariables.write_target_property
        # )

    @staticmethod
    def write_include_directories(context, cmake_file):
        """
        Write include directories of given context to given CMakeLists.txt file

        :param context: current context data
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        has_includes = is_settings_has_data(context.sln_configurations_map,
                                            context.settings,
                                            'inc_dirs')
        if has_includes:
            CMakeWriter.write_comment(cmake_file, 'Include directories')

        include_directories_specifier = 'PUBLIC'
        if context.private_include_directories:
            include_directories_specifier = 'PRIVATE'

        CMakeWriter.write_property_of_settings(
            context, cmake_file,
            begin_text='target_include_directories(${{PROJECT_NAME}} {}'.format(
                include_directories_specifier
            ),
            end_text=')',
            property_name='inc_dirs',
            separator=';\n',
            in_quotes=True
        )
        if has_includes:
            cmake_file.write('\n')

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
        CMakeWriter.write_comment(cmake_file, 'Compile definitions')
        CMakeWriter.write_property_of_settings(
            context, cmake_file,
            begin_text='target_compile_definitions(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=defines,
            separator=';\n',
            in_quotes=True
        )
        for file in context.file_contexts:
            CMakeWriter.write_property_of_settings(
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
        CMakeWriter.write_property_of_settings(
            context, cmake_file,
            begin_text='target_compile_options(${PROJECT_NAME} PRIVATE',
            end_text=')',
            property_name=compiler_flags_key,
            separator=';\n',
            indent=context.indent
        )
        for file in context.file_contexts:
            file_cl_var = 'FILE_CL_OPTIONS'
            text = CMakeWriter.write_property_of_settings(
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
        CMakeWriter.write_property_of_settings(
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

        CMakeWriter.__write_compile_flags(context, cmake_file, compiler_flags_key)
        CMakeWriter.__write_link_flags(context, cmake_file, linker_flags_key)

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

        CMakeWriter.write_comment(cmake_file, 'Compile and link options')
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
    def write_build_event_of_setting(cmake_file, property_indent, config_condition_expr,
                                     property_value, width, **kwargs):
        """ Write target build event functor (helper) """
        if config_condition_expr is None:
            return
        if 'commands' not in property_value:
            return
        for build_event_command in property_value['commands']:
            cmake_file.write('{0}{1}COMMAND {2:>{width}} {3}\n'
                             .format(property_indent, kwargs['main_indent'], config_condition_expr,
                                     build_event_command,
                                     width=width))

    def write_target_build_events(self, context, cmake_file):
        """ Writes all target build events into CMakeLists.txt """
        self.__write_target_build_events_of_context(context, cmake_file, '')

        for file in context.file_contexts:
            file_context = context.file_contexts[file]
            self.__write_target_build_events_of_context(file_context, cmake_file, file)

    def __write_target_build_events_of_context(self, context, cmake_file, depends):
        """ Writes all target build events of given context into CMakeLists.txt """
        self.__write_target_pre_build_events(context, cmake_file, depends)
        self.__write_target_pre_link_events(context, cmake_file, depends)
        self.__write_target_post_build_events(context, cmake_file, depends)
        self.__write_custom_build_events(context, cmake_file, depends)

    def __write_target_pre_build_events(self, context, cmake_file, depends):
        """ Writes target pre build events into CMakeLists.txt """
        self.__write_target_build_events(
            context,
            cmake_file,
            'pre_build_events',
            depends,
            '{0}TARGET ${{PROJECT_NAME}}\n{0}PRE_BUILD\n'.format(context.indent)
        )

    def __write_target_pre_link_events(self, context, cmake_file, depends):
        """ Writes target pre link events into CMakeLists.txt """
        self.__write_target_build_events(
            context,
            cmake_file,
            'pre_link_events',
            depends,
            '{0}TARGET ${{PROJECT_NAME}}\n{0}PRE_LINK\n'.format(context.indent)
        )

    def __write_target_post_build_events(self, context, cmake_file, depends):
        """ Writes target post build events into CMakeLists.txt """
        self.__write_target_build_events(
            context,
            cmake_file,
            'post_build_events',
            depends,
            '{0}TARGET ${{PROJECT_NAME}}\n{0}POST_BUILD\n'.format(context.indent)
        )

    def __write_custom_build_events(self, context, cmake_file, depends):
        """ Writes custom build events of files into CMakeLists.txt """
        self.__write_target_build_events(
            context,
            cmake_file,
            'custom_build_events',
            depends,
            ''
        )

    @staticmethod
    def __write_target_build_events(context, cmake_file, value_name, depends,
                                    commands_head):
        """ Common routine to write down build target events into cmake file"""
        commands = []
        outputs = ''
        comment = ''
        for setting in context.settings:
            settings = context.settings[setting]
            if settings[value_name]:
                if 'commands' in settings[value_name]:
                    commands += settings[value_name]['commands']
                if 'output' in settings[value_name]:
                    outputs = settings[value_name]['output']
                if 'comment' in settings[value_name]:
                    comment = settings[value_name]['comment']
        if commands:
            cmake_comment = value_name.replace('_', ' ').capitalize()
            outputs_str = ''
            if outputs:
                outputs_str = '{0}OUTPUT "{1}"\n'.format(context.indent, outputs)
            depends_str = ''
            if depends:
                depends_str = '{0}DEPENDS "{1}"\n'.format(context.indent, depends)
                cmake_comment += ' of {}'.format(depends)
            comment_str = ''
            if comment:
                comment_str = '{0}COMMENT "{1}"\n'.format(context.indent, comment)

            CMakeWriter.write_comment(cmake_file, cmake_comment)
            text = CMakeWriter.write_property_of_settings(
                context, cmake_file,
                begin_text='add_custom_command_if(\n{1}{2}'
                           '{0}COMMANDS'.format(context.indent, commands_head, outputs_str),
                end_text=depends_str + comment_str + ')',
                property_name=value_name,
                write_setting_property_func=CMakeWriter.write_build_event_of_setting
            )
            if text:
                cmake_file.write('\n')

    @staticmethod
    def write_sln_dependencies(context, cmake_file):
        """
        Write target sln dependencies on given CMakeLists.txt file

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        # Ignore sln-dependency when it matches target reference
        sln_deps_to_write = []
        for sln_dep in context.sln_deps:
            if sln_dep not in context.target_references:
                sln_deps_to_write.append(sln_dep)

        if sln_deps_to_write:
            cmake_file.write('add_dependencies(${PROJECT_NAME}\n')
            for dep in sorted(sln_deps_to_write):
                cmake_file.write('{}{}\n'.format(context.indent, dep))
            cmake_file.write(')\n\n')

    @staticmethod
    def write_link_dependencies(context, cmake_file):
        """
        Write link dependencies of project to given cmake file

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        target_link_specifier = 'PUBLIC'
        configuration_type = None
        for s in context.settings:
            if None in s:
                continue
            configuration_type = context.settings[s]['target_type']
            if configuration_type:
                break

        if configuration_type == 'Application':
            target_link_specifier = 'PRIVATE'

        if context.target_references:
            cmake_file.write('# Link with other targets.\n')
            cmake_file.write('target_link_libraries(${{PROJECT_NAME}} {}\n'
                             .format(target_link_specifier))
            for reference in context.target_references:
                cmake_file.write('{}{}\n'.format(context.indent, reference))
                msg = 'External library found : {}'.format(reference)
                message(context, msg, '')
            cmake_file.write(')\n\n')

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'add_lib_deps'):
            CMakeWriter.write_property_of_settings(
                context, cmake_file,
                begin_text='set(ADDITIONAL_LIBRARY_DEPENDENCIES',
                end_text=')',
                property_name='add_lib_deps',
                separator=';\n',
                in_quotes=True,
            )
            cmake_file.write(
                'target_link_libraries(${{PROJECT_NAME}} {} '
                '"${{ADDITIONAL_LIBRARY_DEPENDENCIES}}")\n\n'.format(
                    target_link_specifier
                )
            )

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'target_link_dirs'):
            CMakeWriter.write_property_of_settings(
                context, cmake_file,
                begin_text='target_link_directories(${{PROJECT_NAME}} {}'
                .format(target_link_specifier),
                end_text=')',
                property_name='target_link_dirs',
                separator=';\n',
                in_quotes=True
            )
            cmake_file.write('\n')

    @staticmethod
    def write_target_dependency_packages(context, cmake_file):
        """
        Write target dependency packages of current context

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        for package in context.packages:
            for package_property in package[2]:
                id_version = '{}.{}'.format(package[0], package[1])
                for setting in context.settings:
                    if 'packages' not in context.settings[setting]:
                        continue
                    if id_version not in context.settings[setting]['packages']:
                        continue
                    if package_property not in context.settings[setting]['packages'][id_version]:
                        continue
                    context.settings[setting][id_version + package_property] =\
                        context.settings[setting]['packages'][id_version][package_property]

                package_property_variable = package_property + '_VAR'
                has_written = CMakeWriter.write_property_of_settings(
                    context, cmake_file,
                    begin_text='string(CONCAT "{}"'.format(package_property_variable),
                    end_text=')',
                    property_name=id_version + package_property,
                )
                if has_written:
                    cmake_file.write(
                        'set_target_properties(${{PROJECT_NAME}} PROPERTIES "{}" ${{{}}})\n'
                        .format(package_property, package_property_variable)
                    )
            cmake_file.write(
                'use_package(${{PROJECT_NAME}} {} {})\n'.format(package[0], package[1])
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

    def write_project_cmake_file(
            self,
            project_context,
            configuration_types_list,
            subdirectories_set,
            subdirectories_to_target_name
    ):
        """ Routine that writes entry point of converted solution for CMake """

        if project_context.dry:
            return

        project_cmake_projects_text = ''
        for project_cmake in get_cmake_lists(project_context, project_context.solution_path, 'r'):
            if project_cmake is not None:
                project_cmake_projects_text = project_cmake.read()

        for project_cmake in get_cmake_lists(project_context, project_context.solution_path):
            project_cmake.write('cmake_minimum_required(VERSION 3.16.0 FATAL_ERROR)\n\n')
            if project_context.target_windows_version:
                project_cmake.write(
                    'set(CMAKE_SYSTEM_VERSION {} CACHE STRING "" FORCE)\n\n'
                    .format(project_context.target_windows_version)
                )

            project_cmake.write(
                'project({} {})\n\n'.format(
                    project_context.project_name,
                    ' '.join(sorted(project_context.project_languages))
                )
            )

            self.write_arch_types(project_context, project_cmake)

            self.__write_supported_architectures_check(project_context, project_cmake)
            self.__write_global_configuration_types(
                project_context, project_cmake, configuration_types_list
            )

            self.__write_global_compile_options(
                project_context, project_cmake, configuration_types_list
            )

            self.__write_global_link_options(
                project_context,
                project_cmake,
                configuration_types_list
            )

            self.write_use_package_stub(project_context, project_cmake)

            CMakeWriter.write_comment(project_cmake, 'Common utils')
            project_cmake.write('include(CMake/Utils.cmake)\n\n')

            CMakeWriter.write_comment(
                project_cmake, 'Additional Global Settings(add specific info there)'
            )
            project_cmake.write('include(CMake/GlobalSettingsInclude.cmake OPTIONAL)\n\n')

            CMakeWriter.write_comment(project_cmake, 'Use solution folders feature')
            project_cmake.write('set_property(GLOBAL PROPERTY USE_FOLDERS ON)\n\n')

            self.__write_subdirectories(
                project_cmake, subdirectories_set, subdirectories_to_target_name
            )

            if project_cmake_projects_text:
                project_cmake.write('\n' * 26)
                project_cmake.write(project_cmake_projects_text)

        warnings = ''
        if project_context.warnings_count > 0:
            warnings = ' ({} warnings)'.format(project_context.warnings_count)
        message(
            project_context,
            'Conversion of {0} finished{1}\n\nNow you may run cmake like following samples:\n\n'
            'to generate:\n'
            'cmake -S "{2}" -B "{3}" -G "Visual Studio 15 2017 Win64"\n'
            '    or\n'
            'cmake -S "{2}" -B "{3}" -G "Visual Studio 16 2019" -A "x64"\n\n'
            'to build:\n'
            'cmake --build "{3}"'.format(
                project_context.vcxproj_path,
                warnings,
                project_context.cmake,
                os.path.join(project_context.cmake, 'build')
            ),
            'done'
        )

    @staticmethod
    def write_arch_types(context, cmake):
        """ Writes setting default architecture """
        CMakeWriter.write_comment(
            cmake,
            'Set target arch type if empty. Visual studio solution generator provides it.'
        )
        cmake.write('if(NOT CMAKE_VS_PLATFORM_NAME)\n')
        cmake.write('{}set(CMAKE_VS_PLATFORM_NAME "x64")\n'.format(context.indent))
        cmake.write('endif()\n')
        cmake.write('message(\"${CMAKE_VS_PLATFORM_NAME} architecture in use\")\n\n')

    @staticmethod
    def write_use_package_stub(context, cmake):
        """ Write use_package CMake routine default implementation """
        CMakeWriter.write_comment(cmake, 'Nuget packages function stub.')
        cmake.write('function(use_package TARGET PACKAGE VERSION)\n')
        cmake.write(
            '{0}message(WARNING "No implementation of use_package. Create yours. "\n'
            '{0}                "Package \\"${{PACKAGE}}\\" with version \\"${{VERSION}}\\" "\n'
            '{0}                "for target \\"${{TARGET}}\\" is ignored!")\n'
            .format(context.indent)
        )
        cmake.write('endfunction()\n\n')

    @staticmethod
    def __write_supported_architectures_check(context, cmake_file):
        arch_list = list(context.supported_architectures)
        arch_list.sort()
        cmake_file.write('if(NOT (')
        first = True
        for arch in arch_list:
            if first:
                cmake_file.write('\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{}\"'
                                 .format(arch))
                first = False
            else:
                cmake_file.write('\n{} OR \"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{}\"'
                                 .format(context.indent, arch))
        cmake_file.write('))\n')
        cmake_file.write(
            '{}message(FATAL_ERROR "${{CMAKE_VS_PLATFORM_NAME}} arch is not supported!")\n'
            .format(context.indent)
        )
        cmake_file.write('endif()\n\n')

    @staticmethod
    def __write_global_configuration_types(context, project_cmake, configuration_types_list):
        CMakeWriter.write_comment(project_cmake, 'Global configuration types')
        project_cmake.write('set(CMAKE_CONFIGURATION_TYPES\n')
        for configuration_type in configuration_types_list:
            project_cmake.write('{}\"{}\"\n'.format(context.indent, configuration_type))
        project_cmake.write('{}CACHE STRING "" FORCE\n)\n\n'.format(context.indent))

    def __write_global_compile_options(
            self,
            project_context, project_cmake,
            configuration_types_list
    ):
        CMakeWriter.write_comment(project_cmake, 'Global compiler options')
        project_cmake.write('if(MSVC)\n')
        project_cmake.write(
            '{}# remove default flags provided with CMake for MSVC\n'.format(project_context.indent)
        )
        have_fortran = False
        for lang in sorted(project_context.project_languages):
            if lang == 'Fortran':
                have_fortran = True
                continue
            self.__write_global_compile_options_language(
                project_context, project_cmake, configuration_types_list, lang
            )
        project_cmake.write('endif()\n\n')

        if have_fortran:
            project_cmake.write('if(${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel")\n')
            project_cmake.write(
                '{}# remove default flags provided with CMake for ifort\n'
                .format(project_context.indent)
            )
            self.__write_global_compile_options_language(
                project_context, project_cmake, configuration_types_list, 'Fortran'
            )
            project_cmake.write('endif()\n\n')

    @staticmethod
    def __write_global_compile_options_language(
            context, project_cmake, configuration_types_list, lang
    ):
        project_cmake.write('{}set(CMAKE_{}_FLAGS "")\n'.format(context.indent, lang))
        for configuration_type in configuration_types_list:
            project_cmake.write('{}set(CMAKE_{}_FLAGS_{} "")\n'
                                .format(context.indent, lang, configuration_type.upper()))

    @staticmethod
    def __write_global_link_options(context, project_cmake, configuration_types_list):
        CMakeWriter.write_comment(project_cmake, 'Global linker options')
        project_cmake.write('if(MSVC)\n')
        project_cmake.write(
            '{}# remove default flags provided with CMake for MSVC\n'.format(context.indent)
        )
        project_cmake.write('{}set(CMAKE_EXE_LINKER_FLAGS "")\n'.format(context.indent))
        project_cmake.write('{}set(CMAKE_MODULE_LINKER_FLAGS "")\n'.format(context.indent))
        project_cmake.write('{}set(CMAKE_SHARED_LINKER_FLAGS "")\n'.format(context.indent))
        project_cmake.write('{}set(CMAKE_STATIC_LINKER_FLAGS "")\n'.format(context.indent))
        for configuration_type in configuration_types_list:
            ct_upper = configuration_type.upper()
            project_cmake.write(
                '{}set(CMAKE_EXE_LINKER_FLAGS_{} \"${{CMAKE_EXE_LINKER_FLAGS}}\")\n'
                .format(context.indent, ct_upper))
            project_cmake.write(
                '{}set(CMAKE_MODULE_LINKER_FLAGS_{} \"${{CMAKE_MODULE_LINKER_FLAGS}}\")\n'
                .format(context.indent, ct_upper))
            project_cmake.write(
                '{}set(CMAKE_SHARED_LINKER_FLAGS_{} \"${{CMAKE_SHARED_LINKER_FLAGS}}\")\n'
                .format(context.indent, ct_upper))
            project_cmake.write(
                '{}set(CMAKE_STATIC_LINKER_FLAGS_{} \"${{CMAKE_STATIC_LINKER_FLAGS}}\")\n'
                .format(context.indent, ct_upper))
        project_cmake.write('endif()\n\n')

    @staticmethod
    def __write_subdirectories(project_cmake, subdirectories_set, subdirectories_to_target_name):
        CMakeWriter.write_comment(project_cmake, 'Sub-projects')
        subdirectories = list(subdirectories_set)
        subdirectories.sort(key=str.lower)
        for subdirectory in subdirectories:
            binary_dir = ''
            if '.' in subdirectory[:1]:
                binary_dir = ' ${{CMAKE_BINARY_DIR}}/{}'.format(
                    subdirectories_to_target_name[subdirectory])
            project_cmake.write('add_subdirectory({}{})\n'.format(
                set_unix_slash(subdirectory), binary_dir))
        project_cmake.write('\n')

    @staticmethod
    def get_comment(text):
        """ Get comment block for given text """
        line_length = 80
        title_line = ''

        for _ in range(0, line_length):
            title_line = '{}{}'.format(title_line, '#')

        comment = title_line + '\n'
        comment += '# {}\n'.format(text)
        comment += title_line + '\n'
        return comment

    @staticmethod
    def write_comment(cmake_file, text):
        """
        Write formatted comment in given file wrapper

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        :param text: text in middle of title
        :type text: str
        """

        cmake_file.write(CMakeWriter.get_comment(text))

    @staticmethod
    def get_str_value_from_property_value(property_value, separator):
        """ Evaluate string value of property """
        if isinstance(property_value, list):
            return separator.join(property_value)

        raise Exception('property value must be a list')

    @staticmethod
    def write_property_of_setting_f(cmake_file,
                                    property_indent,
                                    config_condition_expr,
                                    property_value,
                                    width,
                                    **kwargs):
        """ Default write property functor """
        del width

        separator = kwargs['separator']
        quotes = '"' if kwargs['in_quotes'] else ''

        prop_value_indent = config_indent = property_indent + kwargs['main_indent']
        config_condition_expr_str = ''
        if config_condition_expr is not None:
            config_condition_expr_str = '$<' + config_condition_expr + ':'

        property_value_str = CMakeWriter.get_str_value_from_property_value(
            property_value, separator
        )
        property_list_str = property_value_str.split('\n')

        if config_condition_expr:
            cmake_file.write(
                '{}{}{}\n'.format(config_indent, quotes + config_condition_expr_str, quotes)
            )
            prop_value_indent = config_indent + kwargs['main_indent']

        for prop in property_list_str:
            cmake_file.write(
                '{}{}\n'.format(prop_value_indent, quotes + prop + quotes)
            )

        if config_condition_expr:
            cmake_file.write('{}{}\n'.format(config_indent, quotes + '>' + quotes))

# pylint: disable=R0914
# pylint: disable=R0913

    @staticmethod
    def write_selected_sln_setting(cmake_file,
                                   settings,
                                   sln_setting_2_project_setting,
                                   sln_setting,
                                   has_property_value,
                                   command_indent,
                                   sln_conf,
                                   config_expressions,
                                   max_config_condition_width,
                                   **kwargs
                                   ):
        """ Routine that writes main info of setting block """
        begin_text = kwargs['begin_text']
        property_name = kwargs['property_name']
        indent = kwargs['indent']
        write_setting_property_func = kwargs['write_setting_property_func']

        mapped_setting = settings[sln_setting_2_project_setting[sln_setting]]
        if property_name in mapped_setting:
            if mapped_setting[property_name]:
                if not has_property_value:
                    begin_text = begin_text.replace('\n', '\n' + indent + command_indent)
                    if begin_text:
                        cmake_file.write('{}{}\n'.format(indent + command_indent, begin_text))
                    has_property_value = True

                config_condition_expr = None
                if sln_conf is not None:
                    config_condition_expr = '$<CONFIG:{}>'.format(sln_conf)
                    config_expressions.append(config_condition_expr)
                write_setting_property_func(cmake_file,
                                            indent + command_indent,
                                            config_condition_expr,
                                            mapped_setting[property_name],
                                            max_config_condition_width,
                                            **kwargs
                                            )
        return has_property_value

    @staticmethod
    def write_footer_of_settings(cmake_file,
                                 command_indent,
                                 config_expressions,
                                 has_property_value,
                                 **kwargs):
        """ Writes footer of settings block (default value and closes block) """
        default = kwargs['default']
        end_text = kwargs['end_text']
        indent = kwargs['indent']

        if has_property_value:
            if default and config_expressions:
                cmake_file.write('{}{}$<$<NOT:$<OR:{}>>:{}>\n'
                                 .format(indent + command_indent, kwargs['main_indent'],
                                         ','.join(config_expressions),
                                         default))
            end_text = end_text.replace('\n', '\n' + indent + command_indent)
            if end_text:
                cmake_file.write('{}{}\n'.format(indent + command_indent, end_text))

    @staticmethod
    def write_property_of_settings(context, cmake_file, **kwargs):
        """
        Write property of given settings.

        :param context: Converter context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        :param kwargs: begin of text
        kwargs:
        indent: indent to use when writing
        indent: str
        default: default text to add
        default: None | str
        separator: separator for property list
        separator: ; | str
        in_quotes: Enclose configuration settings in quotes
        in_quotes: False | bool
        write_setting_property_func: function for writing property for setting
        write_setting_property_func: write_property_of_setting | lambda

        """

        kwargs['main_indent'] = context.indent

        settings = context.settings
        sln_setting_2_project_setting = context.sln_configurations_map

        property_name = kwargs['property_name']

        # defaults
        if 'separator' not in kwargs:
            kwargs['separator'] = ';'
        if 'indent' not in kwargs:
            kwargs['indent'] = ''
        if 'default' not in kwargs:
            kwargs['default'] = None
        if 'in_quotes' not in kwargs:
            kwargs['in_quotes'] = False
        if 'write_setting_property_func' not in kwargs:
            kwargs['write_setting_property_func'] = CMakeWriter.write_property_of_setting_f

        indent = kwargs['indent']

        has_property_value = False

        command_indent = ''
        config_expressions = []
        has_property_value = CMakeWriter.write_selected_sln_setting(
            cmake_file, settings, sln_setting_2_project_setting, (None, None),
            has_property_value,
            command_indent,
            None,
            config_expressions,
            0,
            **kwargs
        )

        CMakeWriter.write_footer_of_settings(cmake_file,
                                             command_indent,
                                             config_expressions,
                                             has_property_value,
                                             **kwargs)

        max_config_condition_width = 0
        settings_of_arch = OrderedDict()
        for sln_setting in sln_setting_2_project_setting:
            arch = sln_setting[1]
            if arch is None:
                continue
            conf = sln_setting[0]
            if conf is not None:
                length = len('$<CONFIG:{}>'.format(conf))
                if length > max_config_condition_width:
                    max_config_condition_width = length
            if arch not in settings_of_arch:
                settings_of_arch[arch] = OrderedDict()
            settings_of_arch[arch][sln_setting] = sln_setting

        single_arch = len(settings_of_arch) == 1
        command_indent = ''
        first_arch = True
        for arch in settings_of_arch:
            has_data = is_settings_has_data(sln_setting_2_project_setting, settings, property_name,
                                            arch)
            if not has_data:
                continue

            if not single_arch:
                command_indent = context.indent
                if first_arch:
                    cmake_file.write('{}if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{}\")\n'
                                     .format(indent, arch))
                else:
                    cmake_file.write('{}elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{}\")\n'
                                     .format(indent, arch))
            first_arch = False
            has_property_value = False
            config_expressions = []
            for sln_setting in settings_of_arch[arch]:
                sln_conf = sln_setting[0]
                if sln_setting_2_project_setting[sln_setting] not in settings:
                    continue

                has_property_value = CMakeWriter.write_selected_sln_setting(
                    cmake_file, settings, sln_setting_2_project_setting, sln_setting,
                    has_property_value,
                    command_indent,
                    sln_conf,
                    config_expressions,
                    max_config_condition_width,
                    **kwargs
                )
            CMakeWriter.write_footer_of_settings(cmake_file,
                                                 command_indent,
                                                 config_expressions,
                                                 has_property_value,
                                                 **kwargs)
        if not first_arch and not single_arch:
            cmake_file.write('{}endif()\n'.format(indent))

        return not first_arch

# pylint: enable=R0914
# pylint: enable=R0913
# pylint: enable=R0904
