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
    DataConverter
    =============
     Manage conversion of data into CMake
"""

import os
from collections import OrderedDict
from multiprocessing import Pool
import shutil

from cmake_converter.data_files import get_cmake_lists
from cmake_converter.flags import Flags
from cmake_converter.utils import write_comment, message, get_mapped_arch, write_arch_types,\
    write_use_package_stub, set_unix_slash
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

    def merge_data_settings(self, context):
        """
        Merge common settings found among configuration settings (reduce copy-paste)

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
                    result_settings_list = []
                    for element in lists_of_items_to_merge[setting]:
                        if element not in set_of_items:
                            result_settings_list.append(element)
                    context.settings[setting][key] = result_settings_list

                merged_order_list = self.__get_order_of_common_settings(
                    lists_of_items_to_merge
                )

                merged_settings[key] = self.__get_common_ordered_settings(
                    merged_order_list,
                    set_of_items
                )

            context.sln_configurations_map[(None, arch)] = (None, mapped_arch)

        if context.file_contexts is not None:
            for file in context.file_contexts:
                self.merge_data_settings(context.file_contexts[file])

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
    def __get_common_ordered_settings(merged_order_list, set_of_items):
        common_ordered_list = []
        for element in merged_order_list:
            if element in set_of_items:
                common_ordered_list.append(element)
                set_of_items.remove(element)
                if not set_of_items:
                    break

        return common_ordered_list

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

    def convert_project(self, context, xml_project_path, cmake_lists_destination_path):
        """
        Method template for data collecting and writing

        """
        # Initialize Context of DataConverter
        if not context.init(xml_project_path, cmake_lists_destination_path):
            message(context, 'Unknown project type at {0}'.format(xml_project_path), 'error')
            return False

        message(context, 'Conversion started: Project {0}'.format(context.project_name), 'done')
        message(context, 'Collecting data for project {0}'.format(context.vcxproj_path), '')
        self.collect_data(context)
        self.verify_data(context)
        self.merge_data_settings(context)
        if context.dry:
            return True
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

        return True

    def run_conversion(self, subdirectory_projects_data):
        results = []
        for project_data in subdirectory_projects_data:
            project_context = project_data['project_context']
            name = project_context.project_number
            message(project_context, '------ Starting {} -------'.format(name), '')
            converted = self.convert_project(
                project_context,
                project_data['project_abs'],
                project_data['subdirectory'],
            )
            message(project_context, '------ Exiting  {} -------'.format(name), '')

            if not converted:
                continue

            project_context = project_data['project_context']
            # Can't return context as a result due PicklingError
            results.append(
                {
                    'cmake': project_context.cmake,
                    'project_name': project_context.project_name,
                    'solution_languages': project_context.solution_languages,
                    'target_windows_ver': project_context.target_windows_version,
                    'warnings_count': project_context.warnings_count
                }
            )
        return results

    def do_conversion(self, root_context, input_data_for_converter):
        input_converter_data_list = []
        for subdirectory in input_data_for_converter:
            input_converter_data_list.append(input_data_for_converter[subdirectory])

        results = []
        if root_context.jobs > 1:
            pool = Pool(root_context.jobs)
            results = pool.map(self.run_conversion, input_converter_data_list)
        else:   # do in main thread
            for data_for_converter in input_converter_data_list:
                results.append(self.run_conversion(data_for_converter))

        return results

    @staticmethod
    def write_root_cmake_file(
            root_context,
            input_root_project_path,
            configuration_types_list,
            subdirectories_set,
            subdirectories_to_project_name
    ):

        if root_context.dry:
            return

        root_cmake = get_cmake_lists(root_context, root_context.solution_path, 'r')
        root_cmake_projects_text = ''
        if root_cmake is not None:
            root_cmake_projects_text = root_cmake.read()
            root_cmake.close()

        root_cmake = get_cmake_lists(root_context, root_context.solution_path)
        root_cmake.write('cmake_minimum_required(VERSION 3.13.0 FATAL_ERROR)\n\n')
        if root_context.target_windows_version:
            root_cmake.write(
                'set(CMAKE_SYSTEM_VERSION {} CACHE STRING "" FORCE)\n\n'
                .format(root_context.target_windows_version)
            )
        root_cmake.write(
            'project({} {})\n\n'.format(
                os.path.splitext(os.path.basename(input_root_project_path))[0],
                ' '.join(sorted(root_context.solution_languages))
            )
        )

        write_arch_types(root_cmake)

        DataConverter.__write_supported_architectures_check(root_context, root_cmake)
        DataConverter.__write_global_configuration_types(root_cmake, configuration_types_list)

        DataConverter.__write_global_compile_options(
            root_context, root_cmake, configuration_types_list
        )

        DataConverter.__write_global_link_options(root_cmake, configuration_types_list)

        write_use_package_stub(root_cmake)

        write_comment(root_cmake, 'Common utils')
        root_cmake.write('include(CMake/Utils.cmake)\n\n')
        DataConverter.copy_cmake_utils(root_context.solution_path)

        write_comment(root_cmake, 'Additional Global Settings(add specific info there)')
        root_cmake.write('include(CMake/GlobalSettingsInclude.cmake OPTIONAL)\n\n')

        write_comment(root_cmake, 'Use solution folders feature')
        root_cmake.write('set_property(GLOBAL PROPERTY USE_FOLDERS ON)\n\n')

        DataConverter.__write_subdirectories(
            root_cmake, subdirectories_set, subdirectories_to_project_name
        )

        if root_cmake_projects_text != '':
            root_cmake.write('\n' * 26)
            root_cmake.write(root_cmake_projects_text)

        root_cmake.close()

        warnings = ''
        if root_context.warnings_count > 0:
            warnings = ' ({} warnings)'.format(root_context.warnings_count)
        message(
            root_context,
            'Conversion of {} finished{}'.format(input_root_project_path, warnings),
            'done'
        )

    @staticmethod
    def __write_supported_architectures_check(context, cmake_file):
        arch_list = list(context.supported_architectures)
        arch_list.sort()
        cmake_file.write('if(NOT (')
        first = True
        for arch in arch_list:
            if first:
                cmake_file.write('\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\"'
                                 .format(arch))
                first = False
            else:
                cmake_file.write('\n     OR \"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\"'
                                 .format(arch))
        cmake_file.write('))\n')
        cmake_file.write(
            '    message(FATAL_ERROR "${CMAKE_VS_PLATFORM_NAME} arch is not supported!")\n')
        cmake_file.write('endif()\n\n')

    @staticmethod
    def copy_cmake_utils(cmake_lists_path):
        utils_path = os.path.join(cmake_lists_path, 'CMake')
        if not os.path.exists(utils_path):
            os.makedirs(utils_path)
        src_dir = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(os.path.join(src_dir, 'utils.cmake'), utils_path + '/Utils.cmake')

    @staticmethod
    def __write_global_configuration_types(root_cmake, configuration_types_list):
        write_comment(root_cmake, 'Global configuration types')
        root_cmake.write('set(CMAKE_CONFIGURATION_TYPES\n')
        for configuration_type in configuration_types_list:
            root_cmake.write('    \"{0}\"\n'.format(configuration_type))
        root_cmake.write('    CACHE STRING "" FORCE\n)\n\n')

    @staticmethod
    def __write_global_compile_options(root_context, root_cmake, configuration_types_list):
        write_comment(root_cmake, 'Global compiler options')
        root_cmake.write('if(MSVC)\n')
        root_cmake.write('    # remove default flags provided with CMake for MSVC\n')
        have_fortran = False
        for lang in sorted(root_context.solution_languages):
            if lang == 'Fortran':
                have_fortran = True
                continue
            DataConverter.__write_global_compile_options_language(
                root_cmake, configuration_types_list, lang
            )
        root_cmake.write('endif()\n\n')

        if have_fortran:
            root_cmake.write('if(${CMAKE_Fortran_COMPILER_ID} STREQUAL "Intel")\n')
            root_cmake.write('    # remove default flags provided with CMake for ifort\n')
            DataConverter.__write_global_compile_options_language(
                root_cmake, configuration_types_list, 'Fortran'
            )
            root_cmake.write('endif()\n\n')

    @staticmethod
    def __write_global_compile_options_language(root_cmake, configuration_types_list, lang):
        root_cmake.write('    set(CMAKE_{}_FLAGS "")\n'.format(lang))
        for configuration_type in configuration_types_list:
            root_cmake.write('    set(CMAKE_{}_FLAGS_{} "")\n'
                             .format(lang, configuration_type.upper()))

    @staticmethod
    def __write_global_link_options(root_cmake, configuration_types_list):
        write_comment(root_cmake, 'Global linker options')
        root_cmake.write('if(MSVC)\n')
        root_cmake.write('    # remove default flags provided with CMake for MSVC\n')
        root_cmake.write('    set(CMAKE_EXE_LINKER_FLAGS "")\n')
        root_cmake.write('    set(CMAKE_MODULE_LINKER_FLAGS "")\n')
        root_cmake.write('    set(CMAKE_SHARED_LINKER_FLAGS "")\n')
        root_cmake.write('    set(CMAKE_STATIC_LINKER_FLAGS "")\n')
        for configuration_type in configuration_types_list:
            ct_upper = configuration_type.upper()
            root_cmake.write(
                '    set(CMAKE_EXE_LINKER_FLAGS_{0} \"${{CMAKE_EXE_LINKER_FLAGS}}\")\n'
                .format(ct_upper))
            root_cmake.write(
                '    set(CMAKE_MODULE_LINKER_FLAGS_{0} \"${{CMAKE_MODULE_LINKER_FLAGS}}\")\n'
                .format(ct_upper))
            root_cmake.write(
                '    set(CMAKE_SHARED_LINKER_FLAGS_{0} \"${{CMAKE_SHARED_LINKER_FLAGS}}\")\n'
                .format(ct_upper))
            root_cmake.write(
                '    set(CMAKE_STATIC_LINKER_FLAGS_{0} \"${{CMAKE_STATIC_LINKER_FLAGS}}\")\n'
                .format(ct_upper))
        root_cmake.write('endif()\n\n')

    @staticmethod
    def __write_subdirectories(root_cmake, subdirectories_set, subdirectories_to_project_name):
        write_comment(root_cmake, 'Sub-projects')
        subdirectories = list(subdirectories_set)
        subdirectories.sort(key=str.lower)
        for subdirectory in subdirectories:
            binary_dir = ''
            if '.' in subdirectory[:1]:
                binary_dir = ' ${{CMAKE_BINARY_DIR}}/{0}'.format(
                    subdirectories_to_project_name[subdirectory])
            root_cmake.write('add_subdirectory({0}{1})\n'.format(
                set_unix_slash(subdirectory), binary_dir))
        root_cmake.write('\n')
