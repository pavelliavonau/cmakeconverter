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
    DataConverter
    =============
     Manage conversion of data into CMake
"""

import os
from collections import OrderedDict
from multiprocessing import Pool
import shutil
import copy

from cmake_converter.data_files import get_cmake_lists
from cmake_converter.utils import message
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

        message(context, 'Collecting data for project {}'.format(context.vcxproj_path), '')
        context.parser.parse(context)

        context.files.find_cmake_target_languages(context)

    def verify_data(self, context):
        """ Verify procedure after gathering information from source project """
        self.__verify_target_types(context)
        if 'vcxproj' in context.vcxproj_path:
            self.__verify_common_language_runtime_target_property(context)
        return self.__verify_configurations_to_parse(context)

    @staticmethod
    def __verify_target_types(context):
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
    def __verify_common_language_runtime_target_property(context):
        target_clr = set()
        for setting in context.settings:
            if None in setting:
                continue
            if context.settings[setting]['COMMON_LANGUAGE_RUNTIME']:
                target_clr.add(context.settings[setting]['COMMON_LANGUAGE_RUNTIME'][0])

        if len(target_clr) > 1:
            message(
                context,
                'Target has different types of common language runtime. CMake does not support it!',
                'warn'
            )

    @staticmethod
    def __verify_configurations_to_parse(context):
        absent_settings = set()
        for setting in context.configurations_to_parse:
            if setting not in context.settings:
                absent_settings.add(setting)

        if len(absent_settings) > 0:
            context.configurations_to_parse -= absent_settings
            message(
                context,
                'There are absent settings at {}: {}\n'
                'skipping conversion. Add lost settings or fix mapping of settings at solution'
                .format(context.vcxproj_path, absent_settings),
                'error'
            )
            return False
        return True

    def merge_data_settings(self, context):
        """
        Merge common settings found among configuration settings (reduce copy-paste)

        :param context:
        :return:
        """

        for key in context.utils.lists_of_settings_to_merge():
            lists_of_items_to_merge = {}
            set_of_items = {}

            # get intersection pass
            for sln_setting in context.sln_configurations_map:
                mapped_setting = context.sln_configurations_map[sln_setting]
                mapped_arch = sln_setting[1]
                if mapped_arch is not None and mapped_arch not in lists_of_items_to_merge:
                    lists_of_items_to_merge[mapped_arch] = OrderedDict()
                if (None, mapped_arch) not in context.settings:
                    context.current_setting = (None, mapped_arch)
                    context.utils.init_context_current_setting(context)

                if key not in context.settings[mapped_setting] \
                        or mapped_setting[0] is None:
                    continue
                settings_list = context.settings[mapped_setting][key]
                if not lists_of_items_to_merge[mapped_arch]:  # first pass
                    set_of_items[mapped_arch] = set(settings_list)

                lists_of_items_to_merge[mapped_arch][sln_setting] = settings_list
                set_of_items[mapped_arch] = set_of_items[mapped_arch].intersection(
                    set(context.settings[mapped_setting][key])
                )

            self.__remove_common_settings_from_context(
                context,
                lists_of_items_to_merge,
                set_of_items,
                key
            )

            merged_order_lists = self.__get_order_of_common_settings(lists_of_items_to_merge)

            merged_settings = self.__get_common_ordered_settings(
                merged_order_lists,
                set_of_items
            )

            for arch, merged_setting in merged_settings.items():
                context.settings[(None, arch)][key] = merged_setting
                context.sln_configurations_map[(None, arch)] = (None, arch)

        if context.file_contexts is not None:
            for file in context.file_contexts:
                self.merge_data_settings(context.file_contexts[file])

    def __remove_common_settings_from_context(
            self, context, lists_of_items_to_merge, set_of_items, key
    ):
        """ Removing common settings from configurations """
        for arch in lists_of_items_to_merge:
            for sln_setting in lists_of_items_to_merge[arch]:
                result_settings_list = []
                for element in lists_of_items_to_merge[arch][sln_setting]:
                    if element not in set_of_items[arch]:
                        result_settings_list.append(element)
                self.__update_settings_at_context(
                    context, sln_setting, key, result_settings_list
                )

    @staticmethod
    def __update_settings_at_context(context, sln_setting, key, settings_to_set):
        if sln_setting not in context.settings:
            context.settings[sln_setting] = \
                copy.deepcopy(context.settings[context.sln_configurations_map[sln_setting]])
        context.sln_configurations_map[sln_setting] = sln_setting
        context.settings[sln_setting][key] = settings_to_set

    @staticmethod
    def __get_order_of_common_settings(lists_of_items_to_merge_arch):
        merged_order_lists = {}
        for arch in lists_of_items_to_merge_arch:
            lists_of_items_to_merge = lists_of_items_to_merge_arch[arch]
            merged_order_lists[arch] = []
            i = 0
            while True:
                out_of_bounds = 0
                for setting in lists_of_items_to_merge:
                    settings_list = lists_of_items_to_merge[setting]
                    if i < len(settings_list):
                        merged_order_lists[arch].append(settings_list[i])
                    else:
                        out_of_bounds += 1

                if out_of_bounds == len(lists_of_items_to_merge):
                    break
                i += 1

        return merged_order_lists

    @staticmethod
    def __get_common_ordered_settings(merged_order_list_arch, set_of_items):
        common_ordered_lists = {}
        for arch in merged_order_list_arch:
            merged_order_list = merged_order_list_arch[arch]
            common_ordered_lists[arch] = []
            for element in merged_order_list:
                if element in set_of_items[arch]:
                    common_ordered_lists[arch].append(element)
                    set_of_items[arch].remove(element)
                    if not set_of_items:
                        break

        return common_ordered_lists

    @staticmethod
    def write_data(context, cmake_file):
        """
        Write data defined in converter.

        :param context: converter context
        :type context: Context
        :param cmake_file: CMakeLists IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        context.writer.write_target_cmake_lists(context, cmake_file)

    def convert_project(self, context, xml_project_path, cmake_lists_destination_path):
        """
        Method template for data collecting and writing

        """
        # Initialize Context of DataConverter
        if not context.init(xml_project_path, cmake_lists_destination_path):
            return False

        message(context, 'Conversion started: Project {}'.format(context.project_name), 'done')
        self.collect_data(context)
        if not self.verify_data(context):
            return False
        self.merge_data_settings(context)
        if context.dry:
            return True

        message(context, f'Writing data for project {context.vcxproj_path}', '')
        if os.path.exists(os.path.join(context.cmake, 'CMakeLists.txt')):
            for cmake_file in get_cmake_lists(context, context.cmake, 'a'):
                cmake_file.write('\n' * 26)
                self.write_data(context, cmake_file)
        else:
            for cmake_file in get_cmake_lists(context, context.cmake):
                self.write_data(context, cmake_file)

        warnings = ''
        if context.warnings_count > 0:
            warnings = ' ({} warnings)'.format(context.warnings_count)
        message(
            context,
            'Conversion done   : Project {}{}'.format(context.project_name, warnings), 'done'
        )

        return True

    def run_conversion(self, subdirectory_targets_data):
        """ Routine that converts projects located at the same directory """
        results = []
        for target_data in subdirectory_targets_data:
            target_context = target_data['target_context']
            number = target_context.target_number
            message(target_context, '------ Starting {} -------'.format(number), '')
            converted = self.convert_project(
                target_context,
                target_data['target_abs'],
                target_data['subdirectory'],
            )
            message(target_context, '------ Exiting  {} -------'.format(number), '')

            if not converted:
                continue

            target_context = target_data['target_context']
            # Can't return context as a result due PicklingError
            results.append(
                {
                    'cmake': target_context.cmake,
                    'target_name': target_context.project_name,
                    'project_languages': target_context.project_languages,
                    'target_windows_ver': target_context.target_windows_version,
                    'warnings_count': target_context.warnings_count
                }
            )
        return results

    def do_conversion(self, project_context, input_data_for_converter):
        """ Executes conversion with given projects input data """
        input_converter_data_list = []
        for subdirectory in input_data_for_converter:
            input_converter_data_list.append(input_data_for_converter[subdirectory])

        results = []
        if project_context.jobs > 1:
            with Pool(project_context.jobs) as pool:
                results = pool.map(self.run_conversion, input_converter_data_list)
        else:   # do in main thread
            for data_for_converter in input_converter_data_list:
                results.append(self.run_conversion(data_for_converter))

        return results

    @staticmethod
    def copy_cmake_utils(cmake_lists_path):
        """ Copy necessary util files into CMake folder """
        utils_path = os.path.join(cmake_lists_path, 'CMake')
        if not os.path.exists(utils_path):
            os.makedirs(utils_path)
        src_dir = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(os.path.join(src_dir, 'utils.cmake'), utils_path + '/Utils.cmake')
