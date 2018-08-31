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
import re

from cmake_converter.dependencies import Dependencies
from cmake_converter.data_files import get_xml_data, get_propertygroup
from cmake_converter.utils import normalize_path, message, prepare_build_event_cmd_line_for_cmake


class VCXDependencies(Dependencies):

    def set_include_dirs(self, context, incl_dir):
        """
        Write on "CMakeLists.txt" include directories required for compilation.

        """

        inc_dirs = self.get_additional_include_directories(
            incl_dir.text, context.current_setting, context
        )
        message(context, 'Include Directories found : {0}'.format(inc_dirs), '')

    def add_target_reference(self, context, attr_name, attr_value, node):
        """
        Find and set references of project to current context

        """

        ref = self.get_dependency_target_name(
            context,
            os.path.join(os.path.dirname(context.vcxproj_path), attr_value)
        )

        context.target_references.append(ref)
        message(context, 'Added reference : {}'.format(ref), '')

    @staticmethod
    def set_target_additional_dependencies(context, dependencies):
        """
        Find and set additional dependencies of current project in context

        """
        list_depends = dependencies.text.replace('%(AdditionalDependencies)', '')
        if list_depends != '':
            add_libs = []
            for d in list_depends.split(';'):
                if d != '%(AdditionalDependencies)':
                    if os.path.splitext(d)[1] == '.lib':
                        add_libs.append(d.replace('.lib', ''))
            message(context, 'Additional Dependencies : {}'.format(add_libs), '')
            context.add_lib_deps = True
            context.settings[context.current_setting]['add_lib_deps'] =\
                '$<SEMICOLON>'.join(add_libs)

    @staticmethod
    def set_target_additional_library_directories(context, additional_library_directories):
        """
        Find and set additional library directories in context

        """

        list_depends = additional_library_directories.text.replace(
            '%(AdditionalLibraryDirectories)', ''
        )
        if list_depends != '':
            message(context, 'Additional Library Directories = {}'.format(list_depends), '')
            add_lib_dirs = []
            for d in list_depends.split(';'):
                d = d.strip()
                if d != '':
                    add_lib_dirs.append(d)
            context.add_lib_dirs = add_lib_dirs

    @staticmethod
    def add_target_property_sheet(context, attr_name, filename, node):
        """
        Find and set in current context property sheets

        """

        parent = node.getparent()
        if 'Label' not in parent.attrib:
            return
        if 'PropertySheets' not in parent.attrib['Label']:
            return
        props_set = set(context.property_sheets)
        label = node.get('Label')
        if label:
            return
        if 'Microsoft.CPP.UpgradeFromVC60' in filename:
            return
        # props_path = os.path.join(os.path.dirname(context.vcxproj_path), filename)
        working_path = os.path.dirname(context.vcxproj_path)
        props_set.add(
            normalize_path(
                context,
                working_path,
                filename,
                False
            ).replace('.props', '.cmake')
        )
        # properties_xml = get_xml_data(context, props_path)
        # if properties_xml:
        #     properties_xml.close()  # TODO collect data from props
        context.property_sheets = sorted(props_set)

    @staticmethod
    def __get_info_from_packages_config(context):
        packages_xml = get_xml_data(context, os.path.join(os.path.dirname(context.vcxproj_path),
                                                          context.packages_config_path))
        if not packages_xml:
            return None
        extension = packages_xml['tree'].xpath('/packages/package')
        packages_xml_data = {}
        for ref in extension:
            package_id = ref.get('id')
            package_version = ref.get('version')
            id_version = '{0}.{1}'.format(package_id, package_version)
            packages_xml_data[id_version] = [package_id, package_version]
        return packages_xml_data

    @staticmethod
    def set_target_dependency_packages(context, attr_name, attr_value, ext_targets):
        for import_project_node in ext_targets:
            targets_file_path = import_project_node.get('Project')
            if targets_file_path is None:
                continue

            context.import_projects.append(targets_file_path)

    def apply_target_dependency_packages(self, context):
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

            if len(context.import_projects) and not id_version:
                message(
                    context,
                    'can not find package version in {} by {} path'.format(
                        context.packages_config_path,
                        targets_file_path,
                    ),
                    'warn'
                )
                return

            ext_properties = []
            if targets_file_path:
                targets_file = get_xml_data(context, targets_file_path)
                if targets_file:
                    property_page_schema_nodes = targets_file['tree']\
                        .xpath('//ns:ItemGroup/ns:PropertyPageSchema',
                               namespaces=targets_file['ns'])

                    if property_page_schema_nodes:
                        for property_page_schema_node in property_page_schema_nodes:
                            xml_schema_path = property_page_schema_node.get('Include')
                            xml_schema_path = xml_schema_path.replace(
                                '$(MSBuildThisFileDirectory)',
                                os.path.dirname(targets_file_path) + '/'
                            )
                            xml_schema_file = get_xml_data(context, xml_schema_path)
                            if xml_schema_file:
                                ext_property_nodes = xml_schema_file['tree'] \
                                    .xpath('//ns:EnumProperty',
                                           namespaces=xml_schema_file['ns'])
                                for ext_property_node in ext_property_nodes:
                                    ext_properties.append(ext_property_node.get('Name'))
                    # TODO: remove next if due specific hack
                    if not ext_properties:
                        ext_property_nodes = targets_file['tree']\
                            .xpath('//ns:PropertyGroup'
                                   '[@Label="Default initializers for properties"]/*',
                                   namespaces=targets_file['ns'])
                        for ext_property_node in ext_property_nodes:
                            ext_properties.append(re.sub(r'{.*\}', '', ext_property_node.tag))
                else:
                    message(
                        context,
                        "Can't open {} file for package properties searching. Download nupkg "
                        "and rerun converter again".format(targets_file_path), 'warn1')

            context.packages.append([package_id, package_version, ext_properties])
            message(context, 'Used package {0} {1}.'
                    .format(package_id, package_version), '')

            for ext_property in ext_properties:
                for setting in context.settings:
                    if 'packages' not in context.settings[setting]:
                        context.settings[setting]['packages'] = {}
                    ext_property_node = context.vcxproj['tree'].xpath(
                        '{0}/ns:{1}'.format(get_propertygroup(setting), ext_property),
                        namespaces=context.vcxproj['ns'])
                    if ext_property_node:
                        if id_version not in context.settings[setting]['packages']:
                            context.settings[setting]['packages'][id_version] = {}
                        context.settings[setting]['packages'][id_version][ext_property] = \
                            ext_property_node[0].text
                        message(context, '{0} property of {1} {2} for {3} is {4}'
                                .format(ext_property,
                                        package_id,
                                        package_version,
                                        setting,
                                        ext_property_node[0].text), '')

    @staticmethod
    def __set_target_build_events(context, build_event_node, value_name, event_type):
        for command in build_event_node:
            if 'Command' not in command.tag:
                continue
            for build_event in command.text.split('\n'):
                build_event = build_event.strip()
                if build_event:
                    cmake_build_event = prepare_build_event_cmd_line_for_cmake(
                        context,
                        build_event
                    )
                    context.settings[context.current_setting][value_name] \
                        .append(cmake_build_event)
                    message(context, '{} event : {}'
                            .format(event_type, cmake_build_event), 'info')

    def set_target_pre_build_events(self, context, node):
        self.__set_target_build_events(
            context,
            node,
            'pre_build_events',
            'Pre build'
        )

    def set_target_pre_link_events(self, context, node):
        self.__set_target_build_events(
            context,
            node,
            'pre_link_events',
            'Pre link'
        )

    def set_target_post_build_events(self, context, node):
        self.__set_target_build_events(
            context,
            node,
            'post_build_events',
            'Post build'
        )

    # TODO: implement
    # def set_custom_build_step(self, context, node):
    #     self.__set_target_build_events(
    #         context,
    #         '{0}/ns:CustomBuildStep/ns:Command',
    #         'custom_build_step',
    #         'Custom build'
    #     )
