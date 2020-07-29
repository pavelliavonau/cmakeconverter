#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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

"""
    Parser for *.vcxproj xml
"""

import re

from cmake_converter.parser import Parser, StopParseException
from cmake_converter.data_files import get_xml_data, get_vcxproj_data
from cmake_converter.utils import get_actual_filename, make_cmake_configuration


class VCXParser(Parser):
    """ Class for parser of *.vcxproj files. """

    def __init__(self):
        Parser.__init__(self)
        self.filters = None

    def get_node_handlers_dict(self, context):
        node_handlers = {}

        node_handlers.update(
            dict.fromkeys(context.flags.flags_handlers.keys(), context.flags.set_flag)
        )

        node_handlers.update({
            'ItemGroup': self.__parse_item_group,
            'Target': self._parse_nodes,
            'ProjectConfiguration': self.do_nothing_node_stub,
            'ConfigurationType': self.__parse_configuration_type,
            'WholeProgramOptimization': self.__parse_whole_program_optimization,
            'CharacterSet': context.flags.set_character_set,
            'PlatformToolset': self.do_nothing_node_stub,
            'PropertyGroup': self.__parse_property_group,
            'ProjectName': context.variables.set_project_name,
            'ProjectGuid': self.do_nothing_node_stub,
            'RootNamespace': context.variables.set_root_namespace,
            'Keyword': context.variables.set_keyword,
            'RestorePackages': self.do_nothing_node_stub,             # no support in CMake
            '_ProjectFileVersion': self.do_nothing_node_stub,
            'VCProjectVersion': self.do_nothing_node_stub,
            'CodeAnalysisRuleSet': self.do_nothing_node_stub,         # no support in CMake
            'CodeAnalysisRules': self.do_nothing_node_stub,           # no support in CMake
            'CodeAnalysisRuleAssemblies': self.do_nothing_node_stub,  # no support in CMake
            'RunCodeAnalysis': self.do_nothing_node_stub,             # no support in CMake
            'SccProjectName': self.do_nothing_node_stub,              # no support in CMake
            'SccAuxPath': self.do_nothing_node_stub,                  # no support in CMake
            'SccLocalPath': self.do_nothing_node_stub,                # no support in CMake
            'SccProvider': self.do_nothing_node_stub,                 # no support in CMake
            'WindowsTargetPlatformVersion': context.variables.set_windows_target_version,
            'ItemDefinitionGroup': self.__parse_item_definition_group,
            'Import': self._parse_nodes,
            'ClInclude': self._parse_nodes,
            'ClCompile': self._parse_nodes,
            'None': self._parse_nodes,
            'Text': self._parse_nodes,
            'Xml': self._parse_nodes,
            'CustomBuild': self._parse_nodes,
            'SubType': self.do_nothing_node_stub,  # no support in CMake
            'PreBuildEvent': context.dependencies.set_target_pre_build_events,
            'PreLinkEvent': context.dependencies.set_target_pre_link_events,
            'PostBuildEvent': context.dependencies.set_target_post_build_events,
            'CustomBuildStep': context.dependencies.set_custom_build_events,
            'ExcludedFromBuild': self.__parse_excluded_from_build,
            'ProjectReference': self._parse_nodes,
            'Project': self.do_nothing_node_stub,  # just GUID at <ProjectReference>
            'Private': self.do_nothing_node_stub,                       # no support in CMake
            'ReferenceOutputAssembly': self.do_nothing_node_stub,       # no support in CMake
            'CopyLocalSatelliteAssemblies': self.do_nothing_node_stub,  # no support in CMake
            'LinkLibraryDependencies': context.dependencies.set_link_library_dependencies,
            'UseLibraryDependencyInputs': self.do_nothing_node_stub,    # no support in CMake
            'AdditionalIncludeDirectories': context.dependencies.set_include_dirs,
            'AdditionalDependencies': context.dependencies.set_target_additional_dependencies,
            'AdditionalLibraryDirectories':
                context.dependencies.set_target_additional_library_directories,
            'DelayLoadDLLs': context.dependencies.set_delay_load_dlls,
            'PreprocessorDefinitions': context.flags.set_defines,
            'PrecompiledHeaderOutputFile': self.do_nothing_node_stub,  # no GenEx at OBJECT_OUTPUTS
            'Link': self._parse_nodes,
            'Lib': self._parse_nodes,
            'ImportGroup': self._parse_nodes,
            'ProjectExtensions': self.do_nothing_node_stub,  # no support in CMake
            'OutputFile': context.variables.set_output_file,
            'ImportLibrary': context.variables.set_import_library,
            'ProgramDatabaseFile': context.variables.set_program_database_file,
            'ProgramDataBaseFileName': self.do_nothing_node_stub,  # no support of GenEx in CMake
            'IntDir': self.do_nothing_node_stub,  # no analog at CMake
            'OutDir': context.variables.set_output_dir,
            'TargetName': self.__parse_target_name_node,
            'EnablePREfast': self.do_nothing_node_stub,     # no support from CMake
            'AdditionalOptions': self.__parse_additional_options,
        })
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
            'None_Include': self.__parse_other_files_include_attr,
            'Text_Include': self.__parse_other_files_include_attr,
            'Xml_Include': self.__parse_other_files_include_attr,
            'CustomBuild_Include': self.__parse_other_files_include_attr,
            'Condition': self.__parse_condition,
            'ProjectReference_Include': context.dependencies.add_target_reference,
            'Target_Name': self.__parse_target_name_attr,
        }
        return attributes_handlers

    def parse(self, context):
        context.xml_data = get_vcxproj_data(context, context.vcxproj_path)
        filters_file = get_actual_filename(context, context.vcxproj_path + '.filters')
        if filters_file is not None:
            self.filters = get_xml_data(context, filters_file)
        tree = context.xml_data['tree']
        root = tree.getroot()
        context.current_node = root
        self._parse_nodes(context, root)
        context.current_node = None
        context.flags.apply_flags_to_context(context)
        context.files.apply_files_to_context(context)
        context.dependencies.apply_target_dependency_packages(context)
        if context.sources:
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

        cmake_setting = make_cmake_configuration(context, setting)
        setting = tuple(cmake_setting.split('|'))

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

    def __parse_other_files_include_attr(self, context, attr_name, value, none_node):
        del attr_name, value

        if 'packages.config' in none_node.attrib['Include']:
            context.packages_config_path = none_node.attrib['Include']
        else:
            self.__parse_file_nodes(context, context.other_project_files, none_node, '')

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
        if file_context is not None:
            self._parse_nodes(file_context, file_node)
            context.warnings_count += file_context.warnings_count

    @staticmethod
    def __parse_excluded_from_build(context, node):
        del node
        context.excluded_from_build = True

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
    def __parse_whole_program_optimization(context, node):
        """
        Set Whole Program Optimization: /GL and /LTCG and INTERPROCEDURAL_OPTIMIZATION

        """

        parent = node.getparent()
        parent_tag = Parser.strip_namespace(parent.tag)
        if parent_tag == 'ClCompile':
            node.tag = 'CompileWholeProgramOptimization'
            context.flags.set_flag(context, node)

        if parent_tag == 'PropertyGroup':
            if node.text in ('true', 'PGInstrument', 'PGOptimize', 'PGUpdate'):
                context.settings[context.current_setting]['INTERPROCEDURAL_OPTIMIZATION'] = ['TRUE']
            else:
                context.settings[context.current_setting]['INTERPROCEDURAL_OPTIMIZATION'] =\
                    ['FALSE']

    @staticmethod
    def __parse_target_name_node(context, node):
        context.variables.set_target_name(context, node.text)

    def __parse_condition(self, context, attr_name, condition_value, node):
        del attr_name

        found = re.search(r".*=='(.*)'", condition_value)
        if not found:
            return

        cmake_setting = make_cmake_configuration(context, found.group(1))
        setting = tuple(cmake_setting.split('|'))
        if setting in context.settings:
            context.current_setting = setting
            context.flags.prepare_context_for_flags(context)
            self.reset_current_setting_after_parsing_node(node)
        else:
            context.current_setting = (None, None)
            raise StopParseException()

    @staticmethod
    def __parse_target_name_attr(context, attr_name, target_name_value, node):
        del context, attr_name, node

        if target_name_value == 'EnsureNuGetPackageBuildImports':
            raise StopParseException()
