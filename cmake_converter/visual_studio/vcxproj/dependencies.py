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
Module that handles dependencies information for C/C++ projects.
"""

import os
import re

from cmake_converter.dependencies import Dependencies
from cmake_converter.data_files import get_xml_data, get_propertygroup
from cmake_converter.utils import normalize_path, message, prepare_build_event_cmd_line_for_cmake, \
    check_for_relative_in_path, cleaning_output, set_native_slash, get_mount_point
from cmake_converter.flags import ln_flags


class VCXDependencies(Dependencies):
    """
    Class that handles dependencies information for C/C++ projects.
    """
    def set_include_dirs(self, context, incl_dir):
        """
        Write on "CMakeLists.txt" include directories required for compilation.

        """

        self.set_additional_include_directories(
            incl_dir.text, context.current_setting, context
        )

    def add_target_reference(self, context, attr_name, attr_value, node):
        """
        Find and set references of project to current context

        """

        del attr_name, node

        ref = self.get_dependency_target_name(
            context,
            os.path.join(os.path.dirname(context.vcxproj_path), attr_value)
        )

        context.target_references.append(ref)
        message(context, 'Added reference : {}'.format(ref), '')

    def set_target_additional_dependencies(self, context, dependencies):
        """ Find and set additional dependencies of current project in context """
        self.set_target_additional_dependencies_impl(context, dependencies.text, r'[;]')

    @staticmethod
    def set_target_additional_library_directories(context, additional_library_directories):
        """
        Find and set additional library directories in context

        """

        list_depends = additional_library_directories.text.replace(
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
            message(context, 'Additional Library Directories = {}'.format(add_lib_dirs), '')
            context.settings[context.current_setting]['target_link_dirs'] = add_lib_dirs

    @staticmethod
    def set_link_library_dependencies(context, node):
        """ Handler for link library dependencies. No support of CMake. Just warning. """
        if None in context.current_setting:
            configuration_type = context.settings[context.current_setting]['target_type']
            if node.text == 'true' and configuration_type == 'StaticLibrary':
                message(
                    context,
                    'LinkLibraryDependencies is true that is not supported with cmake. '
                    'There is a workaround with cmake object libraries but it is hard to '
                    'implement it in converter. '
                    'You should switch LinkLibraryDependencies to false, otherwise you '
                    'might have problems with linking.', 'warn1'
                )

    @staticmethod
    def set_delay_load_dlls(context, node):
        """
        DelayLoadDLLs node handler

        :param context:
        :param node:
        :return:
        """
        if node.text is None:
            return

        if node.text != '':
            libs_list = []
            for spec_lib in node.text.split(';'):
                spec_lib = spec_lib.strip()
                if spec_lib:
                    libs_list.append('/DELAYLOAD:' + spec_lib)
            message(context, 'Delay Load Libraries : {}'.format(libs_list), '')
            context.settings[context.current_setting][ln_flags] += libs_list

    @staticmethod
    def add_target_property_sheet(context, attr_name, filename, node):
        """
        Find and set in current context property sheets

        :param context:
        :param attr_name:
        :param filename:
        :param node:
        :return:
        """

        del attr_name, node

        if 'Microsoft' in filename:  # ignore props provided by Microsoft
            return
        if filename[-8:] == '.targets':  # ignore targets files
            return

        working_path = os.path.dirname(context.vcxproj_path)
        props_cmake_path = normalize_path(
            context,
            working_path,
            filename,
            False
        ).replace('.props', '.cmake')
        props_cmake_path = cleaning_output(context, props_cmake_path)
        message(context, 'cmake from property sheet: {}'.format(props_cmake_path), '')
        context.settings[context.current_setting]['property_sheets'].append(props_cmake_path)

    @staticmethod
    def set_target_dependency_packages(context, attr_name, attr_value, ext_targets):
        """ Collects paths of mentioned *.targets files at context.import_projects """
        del attr_name, attr_value
        for import_project_node in ext_targets:
            targets_file_path = import_project_node.get('Project')
            if targets_file_path is None:
                continue

            drive, _ = os.path.splitdrive(targets_file_path)
            if not drive:  # targets_file_path is not absolute
                mount_point = get_mount_point(context.vcxproj_path)
                targets_file_path = set_native_slash(os.path.join(mount_point, targets_file_path))
                targets_file_path = os.path.normpath(targets_file_path)

            context.import_projects.append(targets_file_path)

    def apply_target_dependency_packages(self, context):
        """
        Trying to apply settings and use Nuget Packages

        :param context:
        :return:
        """
        if not context.packages_config_path:
            return

        packages_xml_data = self.__get_info_from_packages_config(context)
        if packages_xml_data is None:
            return

        for targets_file_path in context.import_projects:
            package_id = ''
            package_version = ''
            id_version = ''
            for id_version_i in packages_xml_data:
                if id_version_i in targets_file_path:
                    id_version = id_version_i
                    package_id = packages_xml_data[id_version_i][0]
                    package_version = packages_xml_data[id_version_i][1]
                    break

            if context.import_projects and not id_version:
                message(
                    context,
                    'can not find package version in {} by {} path'.format(
                        context.packages_config_path,
                        targets_file_path,
                    ),
                    'warn'
                )
                continue

            ext_properties = self.__parse_targets_file_of_nuget_package(context, targets_file_path)
            context.packages.append([package_id, package_version, ext_properties])

            for ext_property in ext_properties:
                for setting in context.settings:
                    if None in setting:
                        continue
                    if 'packages' not in context.settings[setting]:
                        context.settings[setting]['packages'] = {}
                    ext_property_node = context.xml_data['tree'].xpath(
                        '{}/ns:{}'.format(get_propertygroup(setting), ext_property),
                        namespaces=context.xml_data['ns'])
                    if ext_property_node:
                        if id_version not in context.settings[setting]['packages']:
                            context.settings[setting]['packages'][id_version] = {}
                        context.settings[setting]['packages'][id_version][ext_property] = \
                            [ext_property_node[0].text]
                        message(
                            context,
                            '{} property of {} {} for {} is {}'.format(
                                ext_property,
                                package_id,
                                package_version,
                                setting,
                                ext_property_node[0].text),
                            '')

            message(context, 'Used package {} {}.'.format(package_id, package_version), '')

    @staticmethod
    def __get_info_from_packages_config(context):
        """
        Parse packages.config file

        :param context:
        :return:
        """
        packages_xml = get_xml_data(
            context,
            os.path.join(os.path.dirname(context.vcxproj_path), context.packages_config_path)
        )
        if not packages_xml:
            return None
        extension = packages_xml['tree'].xpath('/packages/package')
        packages_xml_data = {}
        for ref in extension:
            package_id = ref.get('id')
            package_version = ref.get('version')
            id_version = '{}.{}'.format(package_id, package_version)
            packages_xml_data[id_version] = [package_id, package_version]
        return packages_xml_data

    @staticmethod
    def __parse_targets_file_of_nuget_package(context, targets_file_path):
        """
        Parse *.targets files

        :param context:
        :param targets_file_path:
        :return:
        """
        ext_properties = []
        if not targets_file_path:
            return ext_properties

        targets_file = get_xml_data(context, targets_file_path)
        if targets_file is None:
            message(
                context,
                "Can't open {} file for package properties searching. Download nupkg "
                "and rerun converter again".format(targets_file_path), 'warn1')
            return ext_properties

        property_page_schema_nodes = targets_file['tree'] \
            .xpath('//ns:ItemGroup/ns:PropertyPageSchema',
                   namespaces=targets_file['ns'])

        if property_page_schema_nodes:
            for property_page_schema_node in property_page_schema_nodes:
                xml_schema_path = property_page_schema_node.get('Include')
                xml_schema_path = set_native_slash(xml_schema_path)
                xml_schema_path = xml_schema_path.replace(
                    '$(MSBuildThisFileDirectory)',
                    os.path.dirname(targets_file_path) + '/'
                )
                xml_schema_file = get_xml_data(context, os.path.normpath(xml_schema_path))
                if xml_schema_file:
                    ext_property_nodes = xml_schema_file['tree'] \
                        .xpath('//ns:EnumProperty',
                               namespaces=xml_schema_file['ns'])
                    for ext_property_node in ext_property_nodes:
                        ext_properties.append(ext_property_node.get('Name'))

        # next is just additional ugly trick for nuget
        if not ext_properties:
            ext_property_nodes = targets_file['tree'] \
                .xpath('//ns:PropertyGroup'
                       '[@Label="Default initializers for properties"]/*',
                       namespaces=targets_file['ns'])
            for ext_property_node in ext_property_nodes:
                ext_properties.append(re.sub(r'{.*\}', '', ext_property_node.tag))

        return ext_properties

    @staticmethod
    def __set_target_build_events(context, build_event_node, value_name, event_type):
        """
        General routine for setting build events

        :param context:
        :param build_event_node:
        :param value_name:
        :param event_type:
        :return:
        """
        commands = []
        comment = ''
        output = ''
        for node in build_event_node:
            if 'Message' in node.tag:
                comment = node.text
                continue
            if 'Outputs' in node.tag:
                output = node.text
                continue
            if 'Command' not in node.tag:
                continue
            if node.text is None:
                continue
            for build_event_command in node.text.split('\n'):
                build_event_command = build_event_command.strip()
                if build_event_command:
                    cmake_build_event_command = prepare_build_event_cmd_line_for_cmake(
                        context,
                        build_event_command
                    )
                    commands.append(cmake_build_event_command)

        if commands:
            context.settings[context.current_setting][value_name]['commands'] = commands
            message(context, '{} event commands : {}'
                    .format(event_type, commands), 'info')
        if comment:
            context.settings[context.current_setting][value_name]['comment'] = comment
        if output:
            context.settings[context.current_setting][value_name]['output'] = output

    def set_target_pre_build_events(self, context, node):
        """
        Setting of pre build event to context

        :param context:
        :param node:
        :return:
        """
        self.__set_target_build_events(
            context,
            node,
            'pre_build_events',
            'Pre build'
        )

    def set_target_pre_link_events(self, context, node):
        """
        Setting of pre link build event to context

        :param context:
        :param node:
        :return:
        """
        self.__set_target_build_events(
            context,
            node,
            'pre_link_events',
            'Pre link'
        )

    def set_target_post_build_events(self, context, node):
        """
        Setting of post build event to context

        :param context:
        :param node:
        :return:
        """
        self.__set_target_build_events(
            context,
            node,
            'post_build_events',
            'Post build'
        )

    def set_custom_build_events(self, context, node):
        """ Setting of custom build event to context """
        self.__set_target_build_events(
            context,
            node,
            'custom_build_events',
            'Custom build'
        )
