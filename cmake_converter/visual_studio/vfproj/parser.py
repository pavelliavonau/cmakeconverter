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

from cmake_converter.utils import message
from cmake_converter.context import ContextInitializer
from cmake_converter.parser import Parser


class VFParser(Parser):

    def __init__(self, context):
        self.node_handlers = {
            'Platforms': self.__parse_platforms,
            'Configurations': self.__parse_configurations,
            'Configuration': self.__parse_configuration,
            'Tool': self.__parse_tool,
            'Files': self.__parse_files,
            'Filter': self.__parse_filter,
        }
        self.attributes_handlers = {
            'Configuration_Name': self.__parse_configuration_name,
            'Configuration_TargetName': self.__parse_target_name,
            'Configuration_OutputDirectory': context.variables.set_output_dir,
            'Configuration_IntermediateDirectory': self.__parse_configuration_intermediate_dir,
            'Configuration_DeleteExtensionsOnClean': self.do_nothing_stub,
            'Configuration_ConfigurationType': self.__parse_configuration_type,
            'VFFortranCompilerTool_PreprocessorDefinitions': self.__parse_preprocessor_definitions,
            'VFFortranCompilerTool_AdditionalIncludeDirectories':
                self.__parse_additional_include_directories,
            'VFFortranCompilerTool_SuppressStartupBanner': context.flags.set_flag,
            'VFFortranCompilerTool_DebugInformationFormat': context.flags.set_flag,
            'VFFortranCompilerTool_Optimization': context.flags.set_flag,
            'VFFortranCompilerTool_Preprocess': context.flags.set_flag,
            'VFFortranCompilerTool_SourceFileFormat': context.flags.set_flag,
            'VFFortranCompilerTool_DebugParameter': context.flags.set_flag,
            'VFFortranCompilerTool_DefaultIncAndUsePath': context.flags.set_flag,
            'VFFortranCompilerTool_FixedFormLineLength': context.flags.set_flag,
            'VFFortranCompilerTool_OpenMP': context.flags.set_flag,
            'VFFortranCompilerTool_DisableSpecificDiagnostics': context.flags.set_flag,
            'VFFortranCompilerTool_Diagnostics': context.flags.set_flag,
            'VFFortranCompilerTool_RealKIND': context.flags.set_flag,
            'VFFortranCompilerTool_LocalVariableStorage': context.flags.set_flag,
            'VFFortranCompilerTool_InitLocalVarToNAN': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointExceptionHandling': context.flags.set_flag,
            'VFFortranCompilerTool_ExtendSinglePrecisionConstants': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointStackCheck': context.flags.set_flag,
            'VFFortranCompilerTool_ExternalNameInterpretation': context.flags.set_flag,
            'VFFortranCompilerTool_StringLengthArgPassing': context.flags.set_flag,
            'VFFortranCompilerTool_ExternalNameUnderscore': context.flags.set_flag,
            'VFFortranCompilerTool_Traceback': context.flags.set_flag,
            'VFFortranCompilerTool_RuntimeChecks': context.flags.set_flag,
            'VFFortranCompilerTool_ArgTempCreatedCheck': context.flags.set_flag,
            'VFFortranCompilerTool_RuntimeLibrary': context.flags.set_flag,
            'VFFortranCompilerTool_DisableDefaultLibSearch': context.flags.set_flag,
            'VFFortranCompilerTool_AdditionalOptions': context.flags.set_flag,
            'VFLinkerTool_OutputFile': context.variables.set_output_file,
            'VFLibrarianTool_OutputFile': context.variables.set_output_file,
            'VFLinkerTool_ImportLibrary': context.variables.set_import_library,
            'VFLibrarianTool_ImportLibrary': context.variables.set_import_library,
            'VFLinkerTool_AdditionalDependencies':
                context.dependencies.set_target_additional_dependencies,
            'VFLibrarianTool_AdditionalDependencies':
                context.dependencies.set_target_additional_dependencies,
            'VFLinkerTool_AdditionalLibraryDirectories':
                context.dependencies.set_target_additional_library_directories,
            'VFLibrarianTool_AdditionalLibraryDirectories':
                context.dependencies.set_target_additional_library_directories,
            'VFPreBuildEventTool_CommandLine':
                context.dependencies.set_target_pre_build_events,
            'VFPreLinkEventTool_CommandLine':
                context.dependencies.set_target_pre_link_events,
            'VFPostBuildEventTool_CommandLine':
                context.dependencies.set_target_post_build_events,
        }

    def __parse_nodes(self, context, root):
        for node in root:
            if node.tag in self.node_handlers:
                self.node_handlers[node.tag](context, node)
            else:
                message(context, 'No handler for {} node.'.format(node.tag), 'warn')

    def __parse_attributes(self, context, root):
        for attr in root.attrib:
            key = '{}_{}'.format(root.tag, attr)
            if key in self.attributes_handlers:
                self.attributes_handlers[key](context, root.get(attr), root)
            else:
                message(context, 'No handler for {} attribute.'.format(attr), 'warn')

    def parse(self, context):
        tree = context.vcxproj['tree']
        root = tree.getroot()
        self.__parse_nodes(context, root)
        context.dependencies.set_target_references(context)

    def __parse_platforms(self, context, node):
        pass

    def __parse_configurations(self, context, configurations_node):
        self.__parse_nodes(context, configurations_node)
        self.remove_unused_settings(context)

    def __parse_configuration(self, context, configuration_node):

        self.__parse_attributes(context, configuration_node)

        if 'target_type' not in context.settings[context.current_setting]:
            context.settings[context.current_setting]['target_type'] = 'Application'

        if 'target_name' not in context.settings[context.current_setting]:
            context.settings[context.current_setting]['target_name'] = context.project_name

        context.flags.prepare_context_for_flags(context)
        self.__parse_nodes(context, configuration_node)
        context.flags.apply_flags_to_context(context)
        context.dependencies.add_current_dir_to_includes(context)
        context.current_setting = None

    @staticmethod
    def __parse_configuration_name(context, name_value, node):
        setting = name_value
        context.current_setting = setting
        ContextInitializer.init_context_setting(context, setting)
        context.variables.apply_default_values(context)

    @staticmethod
    def __parse_target_name(context, target_name_value, node):
        context.settings[context.current_setting]['target_name'] = target_name_value

    @staticmethod
    def __parse_configuration_intermediate_dir(context, intermediate_dir_value, node):
        pass

    @staticmethod
    def __parse_configuration_type(context, configuration_type_value, node):
        configuration_type_value = configuration_type_value.replace('type', '')
        context.settings[context.current_setting]['target_type'] = configuration_type_value

    def __parse_tool(self, context, tool_node):
        tool_name = ''
        for attr in tool_node.attrib:
            if 'Name' == attr:
                tool_name = str(tool_node.get('Name'))
                continue

            key = '{}_{}'.format(tool_name, attr)
            if key in self.attributes_handlers:
                self.attributes_handlers[key](context, attr, tool_node.get(attr), tool_node)
            else:
                message(
                    context,
                    'No handler for {} attribute of {}.'.format(attr, tool_name),
                    'warn'
                )

    @staticmethod
    def __parse_preprocessor_definitions(context, flag_name, preprocessor_definitions_value, node):
        context.settings[context.current_setting]['defines'] = \
            preprocessor_definitions_value.split(';')

    @staticmethod
    def __parse_additional_include_directories(
            context,
            flag_name,
            additional_include_directories_value,
            node
    ):
        context.dependencies.get_additional_include_directories(
            additional_include_directories_value,
            context.current_setting,
            context
        )

    def __parse_files(self, context, files_node):
        pass
        # self.__parse_nodes(context, files_node)

    def __parse_filter(self, context, filter_node):
        pass
        # self.__parse_nodes(context, filter_node)

