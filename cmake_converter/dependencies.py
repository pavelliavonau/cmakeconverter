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
    Dependencies
    ============
     Manage directories and libraries of project dependencies
"""

import ntpath
import os
import re

from cmake_converter.data_files import get_vcxproj_data
from cmake_converter.utils import get_global_project_name_from_vcxproj_file, normalize_path, message
from cmake_converter.utils import write_property_of_settings, cleaning_output, write_comment
from cmake_converter.utils import is_settings_has_data, check_for_relative_in_path,\
    replace_vs_vars_with_cmake_vars


class Dependencies(object):
    """
        Class who find and write dependencies of project, additionnal directories...
    """

    @staticmethod
    def find_target_pre_build_events(context):
        pass

    @staticmethod
    def find_target_pre_link_events(context):
        pass

    @staticmethod
    def find_target_post_build_events(context):
        pass

    @staticmethod
    def find_custom_build_step(context):
        pass

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
        write_property_of_settings(
            cmake_file, context.settings, context.sln_configurations_map,
            'target_include_directories(${PROJECT_NAME} PUBLIC', ')', 'inc_dirs'
        )
        if has_includes:
            cmake_file.write('\n')

    @staticmethod
    def get_additional_include_directories(aid_text, setting, context):
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
        inc_dir = aid_text.replace('$(ProjectDir)', './')
        inc_dir = inc_dir.replace('%(AdditionalIncludeDirectories)', '')
        dirs = []
        dirs_raw = []
        for i in inc_dir.split(';'):
            if i:
                dirs_raw.append(i)
                i = normalize_path(context, working_path, i)
                i = replace_vs_vars_with_cmake_vars(context, i)
                dirs.append(i)
        inc_dirs = ';'.join(dirs)
        context.settings[setting]['inc_dirs'] = inc_dirs
        context.settings[setting]['inc_dirs_list'] = dirs_raw

        return inc_dirs

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
        else:
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
            cmake_file.write('add_dependencies(${PROJECT_NAME}')
            for dep in deps_to_write:
                cmake_file.write(' {0}'.format(dep))
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
            cmake_file.write('target_link_libraries(${PROJECT_NAME}')
            for reference in context.target_references:
                cmake_file.write(' ' + reference)
                msg = 'External library found : {0}'.format(reference)
                message(context, msg, '')
            cmake_file.write(')\n\n')

        if is_settings_has_data(context.sln_configurations_map,
                                context.settings,
                                'add_lib_deps'):
            cmake_file.write('# Link with other additional libraries.\n')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                'target_link_libraries(${PROJECT_NAME}', ')',
                'add_lib_deps', ''
            )

        if context.add_lib_dirs:
            cmake_file.write('if(MSVC)\n')
            cmake_file.write('    target_link_libraries(${PROJECT_NAME}')
            for dep in context.add_lib_dirs:
                cmake_file.write(
                    ' -LIBPATH:' + check_for_relative_in_path(
                        context,
                        cleaning_output(context, dep)
                    )
                )
            cmake_file.write(')\nelseif("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")\n')
            cmake_file.write('    target_link_libraries(${PROJECT_NAME}')
            for dep in context.add_lib_dirs:
                cmake_file.write(
                    ' -L' + check_for_relative_in_path(
                        context,
                        cleaning_output(context, dep)
                    )
                )
            cmake_file.write(')\nendif()\n\n')

    @staticmethod
    def write_target_property_sheets(context, cmake_file):
        """
        Write target property sheets of current context

        :param context: current context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if context.property_sheets:
            cmake_file.write('# Includes for CMake from *.props\n')
            for property_sheet in context.property_sheets:
                cmake_file.write('include({0} OPTIONAL)\n'.format(property_sheet))
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
                id_version = '{0}.{1}'.format(package[0], package[1])
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
                    cmake_file, context.settings,
                    context.sln_configurations_map,
                    'string(CONCAT "{0}"'.format(package_property_variable), ')',
                    id_version + package_property, ''
                )
                if has_written:
                    cmake_file.write(
                        'set_target_properties(${{PROJECT_NAME}} PROPERTIES "{0}" ${{{1}}})\n'
                        .format(package_property, package_property_variable)
                    )
            cmake_file.write(
                'use_package(${{PROJECT_NAME}} {0} {1})\n'.format(package[0], package[1])
            )

    @staticmethod
    def write_target_build_event_of_setting(cmake_file, indent, config_condition_expr,
                                            property_value, width):
        for command in property_value:
            cmake_file.write('{0}    COMMAND {1:>{width}} {2}\n'
                             .format(indent, config_condition_expr, command,
                                     width=width))

    @staticmethod
    def __write_target_build_events(context, cmake_file, comment, value_name, event_type):
        has_build_events = is_settings_has_data(context.sln_configurations_map,
                                                     context.settings,
                                                     value_name)
        if has_build_events:
            write_comment(cmake_file, comment)
            write_property_of_settings(
                cmake_file, context.settings, context.sln_configurations_map,
                'add_custom_command_if(\n'
                '    TARGET ${{PROJECT_NAME}}\n'
                '    {0}\n'
                '    COMMANDS'.format(event_type), ')',
                value_name,
                '',
                None,
                Dependencies.write_target_build_event_of_setting
            )
            cmake_file.write('\n')

    @staticmethod
    def write_file_build_event_of_setting(cmake_file, indent, config_condition_expr,
                                          property_value, width):
        # for command in property_value:
        cmake_file.write('{0}    COMMAND {1:>{width}} {2}\n'
                         .format(indent, config_condition_expr, property_value['command_line'],
                                 width=width))

    @staticmethod
    def __write_file_custom_build_events(context, cmake_file, comment, value_name, event_type):
        has_build_events = is_settings_has_data(context.sln_configurations_map,
                                                     context.settings,
                                                     value_name)
        if has_build_events:
            write_comment(cmake_file, comment)
            files = {}
            for setting in context.settings:
                value_data = context.settings[setting][value_name]
                for key in value_data:
                    files[key] = [value_data[key]['outputs'], value_data[key]['description']]
                    context.settings[setting][key] = value_data[key]

            for file in files:
                write_property_of_settings(
                    cmake_file, context.settings, context.sln_configurations_map,
                    'add_custom_command_if(\n'
                    '    OUTPUT "{0}"\n'
                    '    COMMANDS'.format(files[file][0]),
                    '    DEPENDS "{0}"\n'
                    '    COMMENT "{1}"\n)'.format(file, files[file][1]),
                    file,
                    '',
                    None,
                    Dependencies.write_file_build_event_of_setting
                )
                cmake_file.write('\n')
                for setting in context.settings:
                    if file in context.settings[setting]:
                        context.settings[setting].pop(file, None)

    def write_target_pre_build_events(self, context, cmake_file):
        self.__write_target_build_events(
            context,
            cmake_file,
            'Pre build events',
            'pre_build_events',
            'PRE_BUILD'
        )

    def write_target_pre_link_events(self, context, cmake_file):
        self.__write_target_build_events(
            context,
            cmake_file,
            'Pre link events',
            'pre_link_events',
            'PRE_LINK'
        )

    def write_target_post_build_events(self, context, cmake_file):
        self.__write_target_build_events(
            context,
            cmake_file,
            'Post build events',
            'post_build_events',
            'POST_BUILD'
        )

    def write_custom_build_events_of_files(self, context, cmake_file):
        self.__write_file_custom_build_events(
            context,
            cmake_file,
            'Custom build events of files',
            'file_custom_build_events',
            None
        )

