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

from cmake_converter.context import ContextInitializer
from cmake_converter.parser import Parser, StopParseException


class VFParser(Parser):

    def __init__(self):
        Parser.__init__(self)

    def get_node_handlers_dict(self, context):
        node_handlers = {
            'Platforms': self.do_nothing_node_stub,
            'Configurations': self.__parse_configurations,
            'Configuration': self.__parse_configuration,
            'FileConfiguration': self.__parse_file_configuration,
            'Tool': self._parse_nodes,
            'Files': self.__parse_files,
            'File': self.do_nothing_node_stub,
            'Filter': self.__parse_filter,
            'Globals': self.do_nothing_node_stub,
        }
        return node_handlers

    def get_attribute_handlers_dict(self, context):
        attributes_handlers = {
            'Configuration_Name': self.__parse_configuration_name,
            'FileConfiguration_Name': self.__parse_configuration_name,
            'Configuration_TargetName': self.__parse_target_name,
            'Configuration_OutputDirectory': context.variables.set_output_dir,
            'Configuration_IntermediateDirectory': self.__parse_configuration_intermediate_dir,
            'Configuration_DeleteExtensionsOnClean': self.do_nothing_attr_stub,
            'Configuration_ConfigurationType': self.__parse_configuration_type,
            'Tool_Name': self.__parse_tool_name,
            'VFFortranCompilerTool_PreprocessorDefinitions': self.__parse_preprocessor_definitions,
            'VFFortranCompilerTool_AdditionalIncludeDirectories':
                self.__parse_additional_include_directories,
            'VFFortranCompilerTool_SuppressStartupBanner': context.flags.set_flag,
            'VFFortranCompilerTool_DebugInformationFormat': context.flags.set_flag,
            'VFFortranCompilerTool_Optimization': context.flags.set_flag,
            'VFFortranCompilerTool_InterproceduralOptimizations': context.flags.set_flag,
            'VFFortranCompilerTool_EnableEnhancedInstructionSet': context.flags.set_flag,
            'VFFortranCompilerTool_EnableRecursion': context.flags.set_flag,
            'VFFortranCompilerTool_ReentrantCode': context.flags.set_flag,
            'VFFortranCompilerTool_Preprocess': context.flags.set_flag,
            'VFFortranCompilerTool_SourceFileFormat': context.flags.set_flag,
            'VFFortranCompilerTool_DebugParameter': context.flags.set_flag,
            'VFFortranCompilerTool_DefaultIncAndUsePath': context.flags.set_flag,
            'VFFortranCompilerTool_FixedFormLineLength': context.flags.set_flag,
            'VFFortranCompilerTool_OpenMP': context.flags.set_flag,
            'VFFortranCompilerTool_DisableSpecificDiagnostics': context.flags.set_flag,
            'VFFortranCompilerTool_Diagnostics': self.__parse_diagnostics,
            'VFFortranCompilerTool_WarnDeclarations': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnUnusedVariables': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnIgnoreLOC': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnTruncateSource': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnInterfaces': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnUnalignedData': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_WarnUncalled': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_SuppressUsageMessages': self.__parse_concrete_diagnostics,
            'VFFortranCompilerTool_RealKIND': context.flags.set_flag,
            'VFFortranCompilerTool_LocalVariableStorage': context.flags.set_flag,
            'VFFortranCompilerTool_InitLocalVarToNAN': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointExceptionHandling': context.flags.set_flag,
            'VFFortranCompilerTool_ExtendSinglePrecisionConstants': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointModel': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointSpeculation': context.flags.set_flag,
            'VFFortranCompilerTool_FloatingPointStackCheck': context.flags.set_flag,
            'VFFortranCompilerTool_ExternalNameInterpretation': context.flags.set_flag,
            'VFFortranCompilerTool_StringLengthArgPassing': context.flags.set_flag,
            'VFFortranCompilerTool_ExternalNameUnderscore': context.flags.set_flag,
            'VFFortranCompilerTool_Traceback': context.flags.set_flag,
            'VFFortranCompilerTool_RuntimeChecks': self.__parse_runtime_checks,
            'VFFortranCompilerTool_NullPointerCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_BoundsCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_UninitializedVariablesCheck':
                self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_DescriptorDataTypeCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_DescriptorDataSizeCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_ArgTempCreatedCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_StackFrameCheck': self.__parse_concrete_runtime_checks,
            'VFFortranCompilerTool_RuntimeLibrary': context.flags.set_flag,
            'VFFortranCompilerTool_DisableDefaultLibSearch': context.flags.set_flag,
            'VFFortranCompilerTool_AdditionalOptions': context.flags.set_flag,
            'VFFortranCompilerTool_ModulePath': self.do_nothing_attr_stub,  # TODO?
            'VFFortranCompilerTool_ObjectFile': self.do_nothing_attr_stub,  # TODO?
            'VFFortranCompilerTool_AssemblerListingLocation': self.do_nothing_attr_stub,  # TODO?
            'VFFortranCompilerTool_PdbFile': self.do_nothing_attr_stub,  # TODO?
            'VFFortranCompilerTool_ParallelizerDiagLevel': self.do_nothing_attr_stub,  # obsolete?
            'VFFortranCompilerTool_VectorizerDiagLevel': self.do_nothing_attr_stub,  # obsolete?
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
            'VFResourceCompilerTool_PreprocessorDefinitions':
                self.__parse_preprocessor_definitions,
            'VFResourceCompilerTool_Culture':
                self.do_nothing_attr_stub,
            'VFResourceCompilerTool_ResourceOutputFileName':
                self.do_nothing_attr_stub,  # TODO?
            'VFPreBuildEventTool_ExcludedFromBuild': self.do_nothing_attr_stub,
            'VFPreBuildEventTool_CommandLine':
                context.dependencies.set_target_pre_build_events,
            'VFPreLinkEventTool_ExcludedFromBuild': self.do_nothing_attr_stub,
            'VFPreLinkEventTool_CommandLine':
                context.dependencies.set_target_pre_link_events,
            'VFPostBuildEventTool_ExcludedFromBuild': self.do_nothing_attr_stub,
            'VFPostBuildEventTool_CommandLine':
                context.dependencies.set_target_post_build_events,
            'VFCustomBuildTool_ExcludedFromBuild': self.do_nothing_attr_stub,
            'VFCustomBuildTool_CommandLine':
                context.dependencies.set_custom_build_step,
            'VFCustomBuildTool_Description': self.do_nothing_attr_stub,
            'VFCustomBuildTool_Outputs': self.do_nothing_attr_stub,
            'File_RelativePath': self.__parse_file_relative_path,
            'Filter_Name': self.do_nothing_attr_stub,
            'Filter_Filter': self.do_nothing_attr_stub,  # TODO?
        }
        return attributes_handlers

    def parse(self, context):
        tree = context.vcxproj['tree']
        root = tree.getroot()
        self._parse_nodes(context, root)
        context.files.apply_files_to_context(context)
        context.dependencies.set_target_references(context)

    def __parse_configurations(self, context, configurations_node):
        self._parse_nodes(context, configurations_node)

    def __parse_configuration(self, context, configuration_node):

        if 'target_type' not in context.settings[context.current_setting]:
            context.settings[context.current_setting]['target_type'] = 'Application'

        if 'target_name' not in context.settings[context.current_setting]:
            context.settings[context.current_setting]['target_name'] = context.project_name

        context.flags.prepare_context_for_flags(context)
        self._parse_nodes(context, configuration_node)
        context.flags.apply_flags_to_context(context)
        context.dependencies.add_current_dir_to_includes(context)

    def __parse_file_configuration(self, context, file_configuration_node):
        # TODO: can we use __parse_configuration instead?
        # if 'target_type' not in context.settings[context.current_setting]:
        #     context.settings[context.current_setting]['target_type'] = 'Application'
        #
        # if 'target_name' not in context.settings[context.current_setting]:
        #     context.settings[context.current_setting]['target_name'] = context.project_name

        # context.flags.prepare_context_for_flags(context)
        self._parse_nodes(context, file_configuration_node)
        context.flags.apply_flags_to_context(context)
        # context.dependencies.add_current_dir_to_includes(context)

    def __parse_configuration_name(self, context, attr_name, configuration_name, node):
        setting = configuration_name
        if setting not in context.configurations_to_parse:
            context.current_setting = None
            raise StopParseException()
        context.current_setting = setting
        self.common_diagnostics_value = None
        self.common_runtime_checks_value = None
        ContextInitializer.init_context_setting(context, setting)
        context.variables.apply_default_values(context)
        self.reset_current_setting_after_parsing_node(node)

    @staticmethod
    def __parse_target_name(context, attr_name, target_name_value, node):
        context.settings[context.current_setting]['target_name'] = target_name_value

    @staticmethod
    def __parse_configuration_intermediate_dir(context, attr_name, intermediate_dir_value, node):
        pass

    @staticmethod
    def __parse_configuration_type(context, attr_name, configuration_type_value, node):
        configuration_type_value = configuration_type_value.replace('type', '')
        context.settings[context.current_setting]['target_type'] = configuration_type_value

    @staticmethod
    def __parse_tool_name(context, attr_name, tool_name_value, tool_node):
        if tool_name_value in ['VFMidlTool', 'VFManifestTool']:
            raise StopParseException()
        tool_node.tag = tool_name_value

    @staticmethod
    def __parse_preprocessor_definitions(context, flag_name, preprocessor_definitions_value, node):
        for define in preprocessor_definitions_value.split(';'):
            context.settings[context.current_setting]['defines'].append(define)

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

    def __parse_diagnostics(self, context, attr_name, attr_value, node):
        context.flags.set_flag(context, attr_name, attr_value, node)
        self.common_diagnostics_value = attr_value

    def __parse_concrete_diagnostics(self, context, attr_name, attr_value, node):
        if self.common_diagnostics_value is None:
            context.flags.set_flag(context, attr_name, attr_value, node)

    def __parse_runtime_checks(self, context, attr_name, attr_value, node):
        context.flags.set_flag(context, attr_name, attr_value, node)
        self.common_runtime_checks_value = attr_value

    def __parse_concrete_runtime_checks(self, context, attr_name, attr_value, node):
        if self.common_runtime_checks_value is None:
            context.flags.set_flag(context, attr_name, attr_value, node)

    def __parse_files(self, context, filter_node):
        context.files.init_file_lists_for_include_paths(context)
        self._parse_nodes(context, filter_node)

    def __parse_file_relative_path(self, context, attr_name, attr_value, file_node):
        source_group = ''
        parent = file_node.getparent()
        if Parser.strip_namespace(parent.tag) == 'Filter':
            source_group = parent.attrib['Name']
        file_context = context.files.add_file_from_node(
            context,
            context.sources,
            file_node,
            'RelativePath',
            source_group
        )
        self._parse_nodes(file_context, file_node)
        return

    def __parse_filter(self, context, filter_node):
        self._parse_nodes(context, filter_node)

    def __parse_filter_name(self, context, attr_name, attr_value, file_node):
        self.source_group = attr_value
