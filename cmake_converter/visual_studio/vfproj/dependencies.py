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
Module that handles dependencies information for fortran projects.
"""

from cmake_converter.dependencies import Dependencies
from cmake_converter.utils import message, prepare_build_event_cmd_line_for_cmake,\
    check_for_relative_in_path, cleaning_output


class VFDependencies(Dependencies):
    """
    Class that handles dependencies information for fortran projects.
    """

    @staticmethod
    def set_target_references(context):
        """ Sets target references to context """
        if context.sln_deps:
            context.target_references = context.target_references + context.sln_deps
            message(context, 'References : {}'.format(context.target_references), '')

    def set_target_additional_dependencies(self, context, flag_name, ad_libs, node):
        """ Handles additional link dependencies """
        del flag_name, node
        self.set_target_additional_dependencies_impl(context, ad_libs, r'[; ]+')

    @staticmethod
    def set_target_additional_library_directories(context, flag_name,
                                                  additional_library_directories, node):
        """
        Find and set additional library directories in context

        """
        del flag_name, node

        if additional_library_directories:
            list_depends = additional_library_directories.replace(
                '%(AdditionalLibraryDirectories)', ''
            )
            if list_depends != '':
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    d = d.strip()
                    if d != '':
                        add_lib_dirs.append(
                            check_for_relative_in_path(
                                context,
                                cleaning_output(context, d)
                            )
                        )
                message(context,
                        'Additional Library Directories = {}'.format(add_lib_dirs), '')
                context.settings[context.current_setting]['target_link_dirs'] = add_lib_dirs

    @staticmethod
    def __set_target_build_events(context, node, value_name, event_type, command_value):
        """
        General routine for setting build events

        :param context:
        :param value_name:
        :param event_type:
        :param command_value:
        :return:
        """
        commands = []
        for build_event in command_value.split('\n'):
            build_event = build_event.strip()
            if build_event:
                cmake_build_event = prepare_build_event_cmd_line_for_cmake(
                    context,
                    build_event
                )
                commands.append(cmake_build_event)

        comment = ''
        if 'Description' in node.attrib:
            comment = node.attrib['Description']
        output = ''
        if 'Outputs' in node.attrib:
            output = node.attrib['Outputs']

        event_data = {
            'commands': commands,
            'comment': comment,
            'output': output,
        }
        context.settings[context.current_setting][value_name] = event_data
        message(context, '{} events for {}: {}'
                .format(event_type, context.current_setting, commands), 'info')

    @staticmethod
    def __is_excluded_from_build(node):
        """
        Check weather node content is excluded from build

        :param node:
        :return:
        """
        if 'ExcludedFromBuild' in node.attrib:
            return node.attrib['ExcludedFromBuild'] == 'true'
        return False

    def set_target_pre_build_events(self, context, name, command_value, node):
        """
        Setting of pre build event to context

        :param context:
        :param name:
        :param command_value:
        :param node:
        :return:
        """
        del name

        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            node,
            'pre_build_events',
            'Pre build',
            command_value
        )

    def set_target_pre_link_events(self, context, name, command_value, node):
        """
        Setting of pre link event to context

        :param context:
        :param name:
        :param command_value:
        :param node:
        :return:
        """
        del name

        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            node,
            'pre_link_events',
            'Pre link',
            command_value
        )

    def set_target_post_build_events(self, context, name, command_value, node):
        """
        Setting of post build event to context

        :param context:
        :param name:
        :param command_value:
        :param node:
        :return:
        """
        del name

        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            node,
            'post_build_events',
            'Post build',
            command_value
        )

    def set_custom_build_event(self, context, name, command_value, node):
        """
        Setting of custom build event to context
        :param context:
        :param name:
        :param command_value:
        :param node:
        :return:
        """
        del name

        if self.__is_excluded_from_build(node):
            return
        self.__set_target_build_events(
            context,
            node,
            'custom_build_events',
            'Custom build',
            command_value
        )
