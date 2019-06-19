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
    DataConverter
    =============
     Manage conversion of **.vcxproj** data
"""

import os
from collections import OrderedDict

from cmake_converter.data_files import get_cmake_lists
from cmake_converter.flags import Flags
from cmake_converter.utils import write_comment, message, get_mapped_arch
from cmake_converter.context import Context


class DataConverter:
    """
        Base class for converters
    """

    @staticmethod
    def collect_data(context):
        """
        Collect data for converter.

        """

        context.parser.parse(context)

        context.files.find_cmake_project_languages(context)

    @staticmethod
    def verify_data(context):
        target_types = set()
        for setting in context.settings:
            if None in setting:
                continue
            target_types.add(context.settings[setting]['target_type'])

        if len(target_types) > 1:
            message(
                context,
                'Target has more than one output binary type. CMake does not support it!',
                'warn'
            )

    @staticmethod
    def merge_data_settings(context):
        """

        :param context:
        :return:
        """
        for arch in context.supported_architectures:
            mapped_arch = get_mapped_arch(context.sln_configurations_map, arch)
            context.settings[(None, mapped_arch)] = {}
            context.current_setting = (None, mapped_arch)
            context.utils.init_context_current_setting(context)
            merged_settings = context.settings[(None, mapped_arch)]

            for key in context.utils.lists_of_settings_to_merge():
                lists_of_items_to_merge = OrderedDict()
                set_of_items = set()

                # get intersection pass
                for setting in context.settings:
                    if key not in context.settings[setting] \
                            or setting[1] != mapped_arch \
                            or setting[0] is None:
                        continue
                    settings_list = context.settings[setting][key]
                    if not lists_of_items_to_merge:  # first pass
                        set_of_items = set(settings_list)

                    lists_of_items_to_merge[setting] = settings_list
                    set_of_items = set_of_items.intersection(set(context.settings[setting][key]))

                # removing common settings from configurations
                for setting in lists_of_items_to_merge:
                    settings_list = lists_of_items_to_merge[setting]
                    result_settings_list = []
                    for element in settings_list:
                        if element not in set_of_items:
                            result_settings_list.append(element)
                    context.settings[setting][key] = result_settings_list

                merged_order_list = DataConverter.__get_order_of_common_settings(
                    lists_of_items_to_merge
                )

                # getting ordered common settings
                common_ordered_list = []
                for element in merged_order_list:
                    if element in set_of_items:
                        common_ordered_list.append(element)
                        set_of_items.remove(element)
                        if not set_of_items:
                            break

                merged_settings[key] = common_ordered_list

            context.sln_configurations_map[(None, arch)] = (None, mapped_arch)

        if context.file_contexts is not None:
            for file in context.file_contexts:
                DataConverter.merge_data_settings(context.file_contexts[file])

    @staticmethod
    def __get_order_of_common_settings(lists_of_items_to_merge):
        merged_order_list = []
        i = 0
        while True:
            out_of_bounds = 0
            for setting in lists_of_items_to_merge:
                settings_list = lists_of_items_to_merge[setting]
                if i < len(settings_list):
                    merged_order_list.append(settings_list[i])
                else:
                    out_of_bounds += 1

            if out_of_bounds == len(lists_of_items_to_merge):
                break
            i += 1
        return merged_order_list

    @staticmethod
    def write_data(context, cmake_file):
        """
        Write data defined in converter.

        :param context: converter context
        :type context: Context
        :param cmake_file: CMakeLists IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        context.files.write_cmake_project(context, cmake_file)

        # Add additional code or not
        if context.additional_code is not None:
            context.files.add_additional_code(context, context.additional_code, cmake_file)

        context.files.write_source_groups(context, cmake_file)

        if not context.has_only_headers:
            write_comment(cmake_file, 'Target')
            context.flags.write_target_artifact(context, cmake_file)
            context.flags.write_use_pch_function(context, cmake_file)
            context.dependencies.write_target_property_sheets(context, cmake_file)
            context.variables.write_target_outputs(context, cmake_file)
            context.dependencies.write_include_directories(context, cmake_file)
            context.flags.write_defines(context, cmake_file)
            context.flags.write_flags(context, cmake_file)
            context.dependencies.write_target_pre_build_events(context, cmake_file)
            context.dependencies.write_target_pre_link_events(context, cmake_file)
            context.dependencies.write_target_post_build_events(context, cmake_file)
            context.dependencies.write_custom_build_events_of_files(context, cmake_file)
            if (context.target_references
                    or context.add_lib_deps
                    or context.sln_deps
                    or context.packages):
                write_comment(cmake_file, 'Dependencies')
            context.dependencies.write_target_references(context, cmake_file)
            context.dependencies.write_link_dependencies(context, cmake_file)
            context.dependencies.write_target_dependency_packages(context, cmake_file)
        else:
            Flags.write_target_headers_only_artifact(context, cmake_file)

    def convert(self, context):
        """
        Method template for data collecting and writing

        """
        message(context, 'Conversion started: Project {0}'.format(context.project_name), 'done')
        message(context, 'Collecting data for project {0}'.format(context.vcxproj_path), '')
        self.collect_data(context)
        self.verify_data(context)
        self.merge_data_settings(context)
        if context.dry:
            return
        if os.path.exists(context.cmake + '/CMakeLists.txt'):
            cmake_file = get_cmake_lists(context, context.cmake, 'a')
            cmake_file.write('\n' * 26)
        else:
            cmake_file = get_cmake_lists(context, context.cmake)
        message(context, 'Writing data for project {0}'.format(context.vcxproj_path), '')
        self.write_data(context, cmake_file)
        cmake_file.close()
        warnings = ''
        if context.warnings_count > 0:
            warnings = ' ({} warnings)'.format(context.warnings_count)
        message(
            context,
            'Conversion done   : Project {}{}'.format(context.project_name, warnings), 'done'
        )

    @staticmethod
    def add_cmake_version_required(cmake_file):
        """
        Write CMake minimum required

        :param cmake_file: IO cmake file wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        cmake_file.write('cmake_minimum_required(VERSION 3.13.0 FATAL_ERROR)\n\n')
