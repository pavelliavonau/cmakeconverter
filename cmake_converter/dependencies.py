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
    Dependencies
    ============
     Manage directories and libraries of project dependencies
"""

import ntpath
import os
import re

from cmake_converter.data_files import get_vcxproj_data
from cmake_converter.utils import get_global_project_name_from_vcxproj_file, normalize_path, message
from cmake_converter.utils import write_property_of_settings, write_comment
from cmake_converter.utils import is_settings_has_data, replace_vs_vars_with_cmake_vars, \
    resolve_path_variables_of_vs


class Dependencies:
    """
        Class who find and write dependencies of project, additional directories...
    """

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
            write_comment(cmake_file, 'Include directories')

        include_directories_specifier = 'PUBLIC'
        if context.private_include_directories:
            include_directories_specifier = 'PRIVATE'

        write_property_of_settings(
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
    def set_additional_include_directories(aid_text, setting, context):
        """
        Return additional include directories of given context

        :param aid_text: path to sources
        :type aid_text: str
        :param setting: current setting (Debug|x64, Release|Win32,...)
        :type setting: str
        :param context: current context
        :type context: Context
        :return: include directories of context, separated by semicolons
        :rtype: str
        """

        if not aid_text:
            return

        working_path = os.path.dirname(context.vcxproj_path)
        inc_dir = resolve_path_variables_of_vs(context, aid_text)
        inc_dir = inc_dir.replace('%(AdditionalIncludeDirectories)', '')
        inc_dirs = context.settings[setting]['inc_dirs']
        dirs_raw = []
        for i in inc_dir.split(';'):
            if i:
                dirs_raw.append(i)
                i = normalize_path(context, working_path, i)
                i = replace_vs_vars_with_cmake_vars(context, i)
                inc_dirs.append(i)

        context.settings[setting]['inc_dirs_list'].extend(dirs_raw)

        if inc_dirs:
            message(
                context,
                'Include Directories : {}'.format(context.settings[setting]['inc_dirs']),
                '')

    @staticmethod
    def set_target_additional_dependencies_impl(context, dependencies_text, splitter):
        """ Implementation of Handler for additional link dependencies """
        dependencies_text = dependencies_text.replace('%(AdditionalDependencies)', '')
        add_libs = []
        for d in re.split(splitter, dependencies_text):
            if d:
                d = re.sub(r'\.lib$', '', d, 0, re.IGNORECASE)  # strip lib extension
                add_libs.append(d)

        if add_libs:
            context.add_lib_deps = True
            message(context, 'Additional Dependencies : {}'.format(add_libs), '')
            context.settings[context.current_setting]['add_lib_deps'] = add_libs

    @staticmethod
    def get_dependency_target_name(context, vs_project):
        """
        Return dependency target name

        :param context: the context of converter
        :type context: Context
        :param vs_project: path to ".vcxproj" file
        :type vs_project: str
        :return: target name
        :rtype: str
        """

        vcxproj = get_vcxproj_data(context, vs_project)
        project_name = get_global_project_name_from_vcxproj_file(vcxproj)

        if project_name:
            return project_name

        return os.path.splitext(ntpath.basename(vs_project))[0]

    @staticmethod
    def write_target_references(context, cmake_file):
        """
        Write target references on given CMakeLists.txt file

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        deps_to_write = []
        targets_dependencies_set = set()
        for reference in context.target_references:
            targets_dependencies_set.add(reference)
            deps_to_write.append(reference)
        for sln_dep in context.sln_deps:
            if sln_dep not in targets_dependencies_set:
                targets_dependencies_set.add(sln_dep)
                deps_to_write.append(sln_dep)

        if deps_to_write:
            cmake_file.write('add_dependencies(${PROJECT_NAME}\n')
            for dep in deps_to_write:
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

        if context.target_references:
            cmake_file.write('# Link with other targets.\n')
            cmake_file.write('target_link_libraries(${PROJECT_NAME} PUBLIC\n')
            for reference in context.target_references:
                cmake_file.write('{}{}\n'.format(context.indent, reference))
                msg = 'External library found : {}'.format(reference)
                message(context, msg, '')
            cmake_file.write(')\n\n')

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'add_lib_deps'):
            write_property_of_settings(
                context, cmake_file,
                begin_text='set(ADDITIONAL_LIBRARY_DEPENDENCIES',
                end_text=')',
                property_name='add_lib_deps',
                separator=';\n',
                in_quotes=True,
            )
            cmake_file.write(
                'target_link_libraries(${PROJECT_NAME} PUBLIC '
                '"${ADDITIONAL_LIBRARY_DEPENDENCIES}")\n\n')

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'target_link_dirs'):
            write_property_of_settings(
                context, cmake_file,
                begin_text='target_link_directories(${PROJECT_NAME} PUBLIC',
                end_text=')',
                property_name='target_link_dirs',
                separator=';\n',
                in_quotes=True
            )
            cmake_file.write('\n')

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
                if result_width < 0:
                    result_width = 0
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

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'property_sheets'):
            write_comment(cmake_file, 'Includes for CMake from *.props')
            write_property_of_settings(
                context, cmake_file,
                begin_text='',
                end_text='',
                property_name='property_sheets',
                write_setting_property_func=Dependencies.write_property_sheets
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
                has_written = write_property_of_settings(
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

            write_comment(cmake_file, cmake_comment)
            text = write_property_of_settings(
                context, cmake_file,
                begin_text='add_custom_command_if(\n{1}{2}'
                           '{0}COMMANDS'.format(context.indent, commands_head, outputs_str),
                end_text=depends_str + comment_str + ')',
                property_name=value_name,
                write_setting_property_func=Dependencies.write_build_event_of_setting
            )
            if text:
                cmake_file.write('\n')
