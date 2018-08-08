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

from cmake_converter.dependencies import Dependencies
from cmake_converter.utils import message, prepare_build_event_cmd_line_for_cmake


class VFDependencies(Dependencies):

    @staticmethod
    def add_current_dir_to_includes(context):
        if 'inc_dirs' in context.settings[context.current_setting]:
            message(context, 'Include Directories found : {0}'
                    .format(context.settings[context.current_setting]['inc_dirs']), '')
            context.settings[context.current_setting]['inc_dirs'] += ';${CMAKE_CURRENT_SOURCE_DIR}/'
            context.settings[context.current_setting]['inc_dirs_list'].append('./')
        else:
            message(context, 'Include Directories not found for this project.', '')
            context.settings[context.current_setting]['inc_dirs'] = '${CMAKE_CURRENT_SOURCE_DIR}/'
            context.settings[context.current_setting]['inc_dirs_list'] = ['./']

    @staticmethod
    def set_target_references(context):
        if context.sln_deps:
            context.target_references = context.target_references + context.sln_deps
            message(context, 'References : {}'.format(context.target_references), '')

    @staticmethod
    def set_target_additional_dependencies(context, flag_name, ad_libs, node):
        if ad_libs:
            add_libs = []
            for d in ad_libs.split(';'):
                if d != '%(AdditionalDependencies)':
                    if os.path.splitext(d)[1] == '.lib':
                        add_libs.append(d.replace('.lib', ''))
            context.add_lib_deps = True
            message(context, 'Additional Dependencies = {0}'.format(add_libs), '')
            context.settings[context.current_setting]['add_lib_deps'] =\
                '$<SEMICOLON>'.join(add_libs)

    @staticmethod
    def set_target_additional_library_directories(context, flag_name,
                                                  additional_library_directories, node):
        """
        Find and set additional library directories in context

        """

        if additional_library_directories:
            list_depends = additional_library_directories.replace(
                '%(AdditionalLibraryDirectories)', ''
            )
            if list_depends != '':
                message(context,
                        'Additional Library Directories = {0}'.format(list_depends), '')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    d = d.strip()
                    if d != '':
                        add_lib_dirs.append(d)
                context.add_lib_dirs = add_lib_dirs

    @staticmethod
    def __set_custom_build_events_of_files(context, name, command_value, node):
        file_settings = context.settings
        for setting in file_settings:
            if 'file_custom_build_events' not in context.settings[setting]:
                context.settings[setting]['file_custom_build_events'] = {}
            custom_event_data = {
                'command_line': prepare_build_event_cmd_line_for_cmake(
                    context,
                    node.attrib['CommandLine']
                ),
                'description': node.attrib['Description'],
                'outputs': node.attrib['Outputs'],
            }
            context.settings[setting]['file_custom_build_events'] = custom_event_data

    @staticmethod
    def __set_target_build_events(context, value_name, event_type, command_value):
        context.settings[context.current_setting][value_name] = []
        for build_event in command_value.split('\n'):
            build_event = build_event.strip()
            if build_event:
                cmake_build_event = prepare_build_event_cmd_line_for_cmake(
                    context,
                    build_event
                )
                context.settings[context.current_setting][value_name] \
                    .append(cmake_build_event)
                message(context, '{0} event for {1}: {2}'
                        .format(event_type, context.current_setting, cmake_build_event), 'info')

    @staticmethod
    def __is_excluded_from_build(node):
        if 'ExcludedFromBuild' in node.attrib:
            return 'true' == node.attrib['ExcludedFromBuild']
        return False

    def set_target_pre_build_events(self, context, name, command_value, node):
        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            'pre_build_events',
            'Pre build',
            command_value
        )

    def set_target_pre_link_events(self, context, name, command_value, node):
        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            'pre_link_events',
            'Pre link',
            command_value
        )

    def set_target_post_build_events(self, context, name, command_value, node):
        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            'post_build_events',
            'Post build',
            command_value
        )

    # TODO: implement
    def set_custom_build_step(self, context, name, command_value, node):
        if self.__is_excluded_from_build(node):
            return
        self.__set_custom_build_events_of_files(context, name, command_value, node)
    #     self.__find_target_build_events(
    #         context,
    #         'VFCustomBuildTool',
    #         'custom_build_step',
    #         'Custom build'
    #     )
