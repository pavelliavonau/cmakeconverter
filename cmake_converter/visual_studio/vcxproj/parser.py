#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Pavel Liavonau, liavonlida@gmail.com
#   Matthieu Estrada, ttamalfor@gmail.com
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

import re

from cmake_converter.parser import Parser, StopParseException
from cmake_converter.data_files import get_xml_data
from cmake_converter.utils import get_actual_filename


class VCXParser(Parser):

    def __init__(self):
        Parser.__init__(self)
        self.filters = None

    def get_node_handlers_dict(self, context):
        node_handlers = {
            'ItemGroup': self.__parse_item_group,
            'ProjectConfiguration': self.do_nothing_node_stub,
            'ConfigurationType': self.__parse_configuration_type,
            'CharacterSet': context.flags.set_character_set,
            'PlatformToolset': self.do_nothing_node_stub,
            'PropertyGroup': self.__parse_property_group,
            'RootNamespace': context.variables.set_root_namespace,
            '_ProjectFileVersion': self.do_nothing_node_stub,
            'WindowsTargetPlatformVersion': context.variables.set_windows_target_version,
            'ItemDefinitionGroup': self.__parse_item_definition_group,
            'Import': self._parse_nodes,
            'ClInclude': self._parse_nodes,
            'ClCompile': self._parse_nodes,
            'None': self._parse_nodes,
            'PreBuildEvent': context.dependencies.set_target_pre_build_events,
            'PreLinkEvent': context.dependencies.set_target_pre_link_events,
            'PostBuildEvent': context.dependencies.set_target_post_build_events,
            'ProjectReference': self._parse_nodes,
            'LinkLibraryDependencies': context.dependencies.set_link_library_dependencies,
            'AdditionalIncludeDirectories': context.dependencies.set_include_dirs,
            'AdditionalDependencies': context.dependencies.set_target_additional_dependencies,
            'AdditionalLibraryDirectories':
                context.dependencies.set_target_additional_library_directories,
            'IgnoreSpecificDefaultLibraries':
                context.dependencies.set_target_ignore_specific_default_libraries,
            'PreprocessorDefinitions': context.flags.set_defines,
            'PrecompiledHeader': context.flags.set_flag,
            'PrecompiledHeaderFile': context.flags.set_flag,
            'Link': self._parse_nodes,
            'Lib': self._parse_nodes,
            'ImportGroup': self._parse_nodes,
            'OutputFile': context.variables.set_output_file,
            'ImportLibrary': context.variables.set_import_library,
            'ProgramDatabaseFile': context.variables.set_program_database_file,
            'OutDir': context.variables.set_output_dir,
            'TargetName': self.__parse_target_name_node,
            'UseDebugLibraries': context.flags.set_flag,
            'WholeProgramOptimization': context.flags.set_flag,
            'GenerateDebugInformation': context.flags.set_flag,
            'LinkIncremental': context.flags.set_flag,
            'Optimization': context.flags.set_flag,
            'InlineFunctionExpansion': context.flags.set_flag,
            'IntrinsicFunctions': context.flags.set_flag,
            'StringPooling': context.flags.set_flag,
            'BasicRuntimeChecks': context.flags.set_flag,
            'RuntimeLibrary': context.flags.set_flag,
            'FunctionLevelLinking': context.flags.set_flag,
            'WarningLevel': context.flags.set_flag,
            'SuppressStartupBanner': context.flags.set_flag,
            'TreatWarningAsError': context.flags.set_flag,
            'DebugInformationFormat': context.flags.set_flag,
            'CompileAs': context.flags.set_flag,
            'FloatingPointModel': context.flags.set_flag,
            'RuntimeTypeInfo': context.flags.set_flag,
            'DisableSpecificWarnings': context.flags.set_flag,
            'ConformanceMode': context.flags.set_flag,
            'LanguageStandard': context.flags.set_flag,
            'AdditionalOptions': self.__parse_additional_options,
            'ExceptionHandling': context.flags.set_flag,
            'BufferSecurityCheck': context.flags.set_flag,
            'DiagnosticsFormat': context.flags.set_flag,
            'DisableLanguageExtensions': context.flags.set_flag,
            'TreatWChar_tAsBuiltInType': context.flags.set_flag,
            'ForceConformanceInForLoopScope': context.flags.set_flag,
            'RemoveUnreferencedCodeData': context.flags.set_flag,
            'OpenMPSupport': context.flags.set_flag,
        }
        return node_handlers

    def get_attribute_handlers_dict(self, context):
        attributes_handlers = {
            'ItemGroup_Label': self.do_nothing_attr_stub,
            'PropertyGroup_Label': self.do_nothing_attr_stub,
            'Import_Label': self.do_nothing_attr_stub,
            'Import_Project': context.dependencies.add_target_property_sheet,
            'ImportGroup_Label': self.__parse_import_group_label,
            'ProjectConfiguration_Include': self.__parse_project_configuration_include,
            'ClCompile_Include': self.__parse_cl_compile_include_attr,
            'ClInclude_Include': self.__parse_cl_include_include_attr,
            'None_Include': self.__parse_cl_none_include_attr,
            'Condition': self.__parse_condition,
            'ProjectReference_Include': context.dependencies.add_target_reference,
        }
        return attributes_handlers

    def parse(self, context):
        filters_file = get_actual_filename(context, context.vcxproj_path + '.filters')
        if filters_file is not None:
            self.filters = get_xml_data(context, filters_file)
        tree = context.vcxproj['tree']
        root = tree.getroot()
        self._parse_nodes(context, root)
        context.flags.apply_flags_to_context(context)
        context.files.apply_files_to_context(context)
        context.dependencies.apply_target_dependency_packages(context)
        if not context.has_only_headers:
            context.flags.define_pch_cpp_file(context)

    def __parse_item_group(self, context, node):
        self._parse_nodes(context, node)

    @staticmethod
    def __parse_import_group_label(context, attr_name, attr_value, node):
        if attr_value in ['ExtensionTargets', 'Shared', 'ExtensionSettings']:
            context.dependencies.set_target_dependency_packages(
                context,
                attr_name,
                attr_value,
                node
            )

    @staticmethod
    def __parse_project_configuration_include(context, attr_name, setting,
                                              project_configuration_node):
        del attr_name, project_configuration_node

        setting = tuple(setting.split('|'))

        if setting not in context.configurations_to_parse:
            return

        context.current_setting = setting
        context.utils.init_context_current_setting(context)

        context.current_setting = (None, None)

    @staticmethod
    def __parse_configuration_type(context, node):
        context.settings[context.current_setting]['target_type'] = node.text

    def __parse_item_definition_group(self, context, node):
        self._parse_nodes(context, node)

    def __parse_property_group(self, context, node):
        self._parse_nodes(context, node)

    def __get_source_group_from_filters(self, node, filter_node_name):
        if self.filters:
            file_path = node.attrib['Include']
            filter_node = self.filters['tree'].xpath(
                '//ns:{}[@Include="{}"]/*'.format(filter_node_name, file_path),
                namespaces=self.filters['ns']
            )
            if filter_node:
                return filter_node[0].text.replace('\\', '\\\\')

        return ''

    def __parse_cl_include_include_attr(self, context, attr_name, value, include_node):
        del attr_name, value

        self.__parse_file_nodes(context, context.headers, include_node, 'Headers')
        raise StopParseException()

    def __parse_cl_compile_include_attr(self, context, attr_name, value, cl_node):
        del attr_name, value

        self.__parse_file_nodes(context, context.sources, cl_node, 'Sources')
        raise StopParseException()

    def __parse_cl_none_include_attr(self, context, attr_name, value, none_node):
        del attr_name, value

        self.__parse_file_nodes(context, context.other_project_files, none_node, '')
        if 'packages.config' in none_node.attrib['Include']:
            context.packages_config_path = none_node.attrib['Include']
        raise StopParseException()

    def __parse_file_nodes(self, context, files_container, file_node, source_group):
        if self.filters:
            source_group = self.__get_source_group_from_filters(
                file_node,
                Parser.strip_namespace(file_node.tag)
            )

        file_context = context.files.add_file_from_node(
            context,
            files_container=files_container,
            file_node=file_node,
            file_node_attr='Include',
            source_group=source_group
        )
        self._parse_nodes(file_context, file_node)

    @staticmethod
    def __parse_additional_options(context, node):
        parent = node.getparent()
        parent_tag = Parser.strip_namespace(parent.tag)
        if parent_tag == 'ClCompile':
            node.tag = 'CompileAdditionalOptions'
            context.flags.set_flag(context, node)
        if parent_tag == 'Link':
            node.tag = 'LinkAdditionalOptions'
            context.flags.set_flag(context, node)

    @staticmethod
    def __parse_target_name_node(context, node):
        context.variables.set_target_name(context, node.text)

    def __parse_condition(self, context, attr_name, condition_value, node):
        del attr_name

        found = re.search(r".*=='(.*)'", condition_value)
        if not found:
            return
        setting = tuple(found.group(1).split('|'))
        if setting in context.settings:
            context.current_setting = setting
            context.flags.prepare_context_for_flags(context)
            self.reset_current_setting_after_parsing_node(node)
        else:
            context.current_setting = (None, None)
            raise StopParseException()
