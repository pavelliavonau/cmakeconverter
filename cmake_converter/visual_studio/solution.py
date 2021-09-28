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
Module of Visual Studio solution related logic for converting.
"""

import re
import os
import sys
import shutil
from collections import OrderedDict

from cmake_converter.data_converter import DataConverter
from cmake_converter.utils import message, set_native_slash, make_cmake_configuration


class VSSolutionConverter(DataConverter):
    """
    Implementation of Converter for Visual Studio solution
    """
    def parse_solution(self, context, sln_text):
        """
        Parse given solution
        :param context: context from sln input file
        :type context: Context
        :param sln_text: full solution text
        :type sln_text: str
        :return: data from solution
        :rtype: dict
        """

        solution_data = {}
        sln_projects_data = OrderedDict()
        solution_folders = {}

        self.__check_solution_version(context, sln_text)

        message(context, 'Start parsing projects info (Project .. EndProject)', '')
        self.__parse_sln_projects_data(context, sln_text, solution_folders, sln_projects_data)

        message(context, 'Start parsing GlobalSection(SolutionConfigurationPlatforms) = '
                         'preSolution', '')
        self.__parse_configurations_of_solution(context, sln_text, solution_data)

        message(context, 'Start parsing GlobalSection(ProjectConfigurationPlatforms) = '
                         'postSolution (Mapping sln-setting -> project-setting)', '')
        self.__parse_project_configuration_platforms(context, sln_text, sln_projects_data)

        solution_folders_map = {}

        self.__parse_nested_projects_in_solution_folders(sln_text, solution_folders_map)

        self.set_solution_dirs_to_projects(
            sln_projects_data, solution_folders_map, solution_folders
        )

        # replace GUIDs with Project names in dependencies
        for sln_project_guid in sln_projects_data:
            sln_project_data = sln_projects_data[sln_project_guid]
            if 'sln_deps' in sln_project_data:
                target_deps = []
                dependencies_list = sln_project_data['sln_deps']
                for dep_guid in dependencies_list:
                    if not self.__check_project_guid(context, sln_projects_data, dep_guid):
                        continue
                    dep = sln_projects_data[dep_guid]
                    target_deps.append(dep['name'])
                sln_project_data['sln_deps'] = target_deps
        solution_data['sln_projects_data'] = sln_projects_data

        return solution_data

    @staticmethod
    def __check_project_guid(context, projects_data, project_guid):
        if project_guid not in projects_data:
            message(
                context,
                'project with GUID {} is missing in solution file'.format(project_guid),
                'error'
            )
            return False
        return True

    @staticmethod
    def __check_solution_version(context, sln_text):
        version_pattern = re.compile(
            r'Microsoft Visual Studio Solution File, Format Version (.*)'
        )
        version_match = version_pattern.findall(sln_text)
        if not version_match or float(version_match[0]) < 9:
            message(context, 'Solution files with versions below 9.00 are not supported.'
                             ' Version {} found. Upgrade you solution and try again, please'
                    .format(version_match[0]), 'error')
            sys.exit(1)

        message(context, 'Version of solution is {}'.format(version_match[0]), '')

    @staticmethod
    def __parse_sln_projects_data(context, sln_text, solution_folders, sln_projects_data):
        """
        Parse section with information about project at *.sln file

        :param context: context from input file
        :type context: Context
        :param sln_text:
        :param solution_folders:
        :param sln_projects_data:
        :return:
        """
        p = re.compile(
            r'(Project.*\s=\s\"(.*)\",\s\"(.*)\",.*({.*\})(?:.|\n)*?EndProject(?!Section))'
        )

        for project_data_match in p.findall(sln_text):
            path = set_native_slash(project_data_match[2])
            guid = project_data_match[3]

            _, ext = os.path.splitext(os.path.basename(path))

            if 'proj' not in ext:
                solution_folders[guid] = path
                continue

            sln_projects_data[guid] = VSSolutionConverter.__parse_project_data(
                context, project_data_match, path
            )

    @staticmethod
    def __parse_project_data(context, project_data_match, path):
        """
        Parse project section at *.sln file

        :param context: context from input file
        :type context: Context
        :param project_data_match:
        :param path:
        :return:
        """
        project = {'name': project_data_match[1]}
        message(context, '    Found project "{}" with {}'.format(path, project_data_match[3]), '')
        project['path'] = path
        project['sln_configs_2_project_configs'] = OrderedDict({(None, None): (None, None)})
        if 'ProjectDependencies' in project_data_match[0]:
            project['sln_deps'] = []
            dependencies_section = re.compile(
                r'ProjectSection\(ProjectDependencies\) = '
                r'postProject(?:.|\n)*?EndProjectSection'
            )
            dep_data = dependencies_section.findall(project_data_match[0])
            dependencies_guids = re.compile(r'(({.*\}) = ({.*\}))')
            guids_deps_matches = dependencies_guids.findall(dep_data[0])
            for guids_deps_match in guids_deps_matches:
                project['sln_deps'].append(guids_deps_match[2])
        return project

    @staticmethod
    def __parse_configurations_of_solution(context, sln_text, solution_data):
        solution_configurations_re = re.compile(
            r'GlobalSection\(SolutionConfigurationPlatforms\) = '
            r'preSolution((?:.|\n)*?)EndGlobalSection'
        )

        solution_configurations_matches = solution_configurations_re.findall(sln_text)
        solution_data['sln_configurations'] = []
        sln_configuration_re = re.compile(r'([\w -|]+) = ([\w -|]+)')
        for solution_configuration_match in solution_configurations_matches:
            configurations = sln_configuration_re.findall(solution_configuration_match)
            for sln_configuration in configurations:
                cmake_configuration = make_cmake_configuration(context, sln_configuration[0])
                solution_data['sln_configurations'].append(cmake_configuration)
                message(context, '    Found sln setting "{}"'.format(cmake_configuration), '')
                arch = cmake_configuration.split('|')[1]
                if arch == 'x86':
                    message(
                        context,
                        'Solution architecture is x86 and may be mapped onto Win32 at projects.'
                        'To avoid problems rename x86 -> Win32.',
                        'warn')
                context.supported_architectures.add(arch)

    def __parse_project_configuration_platforms(self, context, sln_text, sln_projects_data):
        projects_configurations_re = re.compile(
            r'GlobalSection\(ProjectConfigurationPlatforms\) = '
            r'postSolution((?:.|\n)*?)EndGlobalSection'
        )
        projects_configurations_matches = projects_configurations_re.findall(sln_text)
        projects_configuration_re = re.compile(r'({.+\})\.([\w -|]+)\.ActiveCfg = ([\w -|]+)')
        for projects_configuration_match in projects_configurations_matches:
            sln_config_groups = projects_configuration_re.findall(projects_configuration_match)
            for sln_config_group in sln_config_groups:
                if not self.__check_project_guid(context, sln_projects_data, sln_config_group[0]):
                    continue
                p = sln_projects_data[sln_config_group[0]]
                sln_cmake_configuration = make_cmake_configuration(context, sln_config_group[1])
                project_cmake_configuration = make_cmake_configuration(context, sln_config_group[2])
                p['sln_configs_2_project_configs'][tuple(sln_cmake_configuration.split('|'))] = \
                    tuple(project_cmake_configuration.split('|'))
                message(
                    context,
                    '    "{}" -> "{}" for {}'.format(
                        sln_cmake_configuration,
                        project_cmake_configuration,
                        p['name']
                    ),
                    ''
                )

    @staticmethod
    def __parse_nested_projects_in_solution_folders(sln_text, solution_folders_map):
        nested_projects_re = re.compile(
            r'GlobalSection\(NestedProjects\) = preSolution((?:.|\n)*?)EndGlobalSection'
        )
        nested_projects_matches = nested_projects_re.findall(sln_text)
        solution_dir_link_re = re.compile(r'(\{.+\}) = (\{.+\})')
        for nested_projects_match in nested_projects_matches:
            solution_dir_links = solution_dir_link_re.findall(nested_projects_match)
            for solution_dir_link in solution_dir_links:
                solution_folders_map[solution_dir_link[0]] = solution_dir_link[1]

    @staticmethod
    def set_solution_dirs_to_projects(projects_data, solution_folders_map, solution_folders):
        """ Evaluate locations of projects in Solution explorer tree of Visual Studio UI """
        for project_guid in projects_data:
            sln_project_folder = ''

            if project_guid in solution_folders_map:
                guid = project_guid
                while guid in solution_folders_map:
                    if sln_project_folder:
                        sln_project_folder = '/' + sln_project_folder
                    sln_project_folder = solution_folders[solution_folders_map[guid]]\
                        + sln_project_folder
                    guid = solution_folders_map[guid]

            projects_data[project_guid]['sln_project_folder'] = sln_project_folder

    @staticmethod
    def set_dependencies_for_project(context, project_data):
        """ Copy dependencies on other solution projects into project context """
        if 'sln_deps' not in project_data:
            return

        context.sln_deps = project_data['sln_deps']

    @staticmethod
    def clean_cmake_lists_file(context, subdirectory, cmake_lists_set):
        """ Clean previous CMake script before converting """
        cmake_path_to_clean = \
            os.path.join(
                context.set_cmake_lists_path(subdirectory),
                'CMakeLists.txt'
            )
        if context.dry:
            return

        if cmake_path_to_clean in cmake_lists_set:
            return
        cmake_lists_set.add(cmake_path_to_clean)

        if os.path.exists(cmake_path_to_clean):
            os.remove(cmake_path_to_clean)
            message(context, 'removed {}'.format(cmake_path_to_clean), '')
        else:
            message(context, 'not found {}'.format(cmake_path_to_clean), 'warn')

    def clean_cmake_lists_of_solution(self, context, sln_projects_data):
        """ Clean previous set of CMake scripts before converting """
        if not os.path.exists(os.path.join(context.solution_path, 'CMake')):
            return  # first run

        message(context, 'Cleaning CMake Scripts', '')
        cmake_lists_set = set()
        for guid in sln_projects_data:
            sln_project_path = sln_projects_data[guid]['path']
            sln_project_abs = os.path.join(context.solution_path, sln_project_path)
            subdirectory = os.path.dirname(sln_project_abs)
            self.clean_cmake_lists_file(context, subdirectory, cmake_lists_set)

        self.clean_cmake_lists_file(context, context.solution_path, cmake_lists_set)
        print('\n')

    def convert_solution(self, project_context, sln_file_path):
        """
        Routine converts Visual studio solution into set of CMakeLists.txt scripts
        """

        message(
            project_context, '------- Started parsing solution {} -------'.format(sln_file_path), ''
        )
        with open(sln_file_path, encoding='utf8') as sln:
            solution_data = self.parse_solution(project_context, sln.read())
        message(
            project_context, '------ Finished parsing solution {} -------'.format(sln_file_path), ''
        )

        project_context.solution_path = os.path.dirname(sln_file_path)
        project_context.project_name = os.path.splitext(os.path.basename(sln_file_path))[0]
        project_context.vcxproj_path = sln_file_path
        subdirectories_set = set()
        subdirectories_to_target_name = {}
        sln_projects_data = solution_data['sln_projects_data']

        self.clean_cmake_lists_of_solution(project_context, sln_projects_data)

        input_data_for_converter = self.__get_input_data_for_converter(
            project_context,
            sln_projects_data
        )

        results = self.do_conversion(project_context, input_data_for_converter)

        self.__get_info_from_results(
            project_context,
            results,
            subdirectories_set,
            subdirectories_to_target_name
        )

        configuration_types_list = self.__get_global_configuration_types(solution_data)

        project_context.writer.write_project_cmake_file(
            project_context,
            configuration_types_list,
            subdirectories_set,
            subdirectories_to_target_name
        )

        self.copy_cmake_utils(project_context.solution_path)

    def __get_input_data_for_converter(self, project_context, sln_projects_data):
        input_data_for_converter = {}
        target_number = 0
        projects_filter_pattern = re.compile(project_context.projects_regexp)
        for guid in sln_projects_data:
            target_number += 1
            target_context = project_context.clone()
            target_context.target_number = target_number
            sln_project_path = sln_projects_data[guid]['path']

            m = projects_filter_pattern.match(sln_project_path)
            if m is None:
                continue

            sln_project_abs = os.path.join(project_context.solution_path, sln_project_path)
            subdirectory = os.path.dirname(sln_project_abs)
            self.set_dependencies_for_project(target_context, sln_projects_data[guid])
            target_context.sln_configurations_map = \
                sln_projects_data[guid]['sln_configs_2_project_configs']
            target_context.project_folder = sln_projects_data[guid]['sln_project_folder']
            if subdirectory not in input_data_for_converter:
                input_data_for_converter[subdirectory] = []
            input_data_for_converter[subdirectory].append(
                {
                    'target_context': target_context,
                    'target_abs': sln_project_abs,
                    'subdirectory': subdirectory
                }
            )

        return input_data_for_converter

    @staticmethod
    def __get_info_from_results(
            project_context,
            results,
            subdirectories_set,
            subdirectories_to_target_name
    ):
        for directory_results in results:
            for sln_target_result in directory_results:
                subdirectory = os.path.relpath(
                    sln_target_result['cmake'], project_context.solution_path
                )
                if subdirectory != '.':
                    subdirectories_set.add(subdirectory)
                subdirectories_to_target_name[subdirectory] = sln_target_result['target_name']
                project_context.project_languages.update(sln_target_result['project_languages'])
                if project_context.target_windows_version and \
                        sln_target_result['target_windows_ver'] and \
                        project_context.target_windows_version !=\
                        sln_target_result['target_windows_ver']:
                    message(
                        project_context,
                        'CMake does not support more than 1 version of windows SDK', 'warn'
                    )
                if sln_target_result['target_windows_ver']:
                    project_context.target_windows_version = \
                        sln_target_result['target_windows_ver']
                project_context.warnings_count += sln_target_result['warnings_count']

    @staticmethod
    def __get_global_configuration_types(solution_data):
        configuration_types_set = set()
        for config in solution_data['sln_configurations']:
            configuration_types_set.add(config.split('|')[0])
        configuration_types_list = list(configuration_types_set)
        configuration_types_list.sort(key=str.lower)
        return configuration_types_list

    def copy_cmake_utils(self, cmake_lists_path):
        super().copy_cmake_utils(cmake_lists_path)

        utils_path = os.path.join(cmake_lists_path, 'CMake')
        if not os.path.exists(utils_path):
            os.makedirs(utils_path)
        src_dir = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(os.path.join(src_dir, 'Default.cmake'), utils_path + '/Default.cmake')
        shutil.copyfile(os.path.join(src_dir, 'DefaultCXX.cmake'),
                        utils_path + '/DefaultCXX.cmake')
        shutil.copyfile(os.path.join(src_dir, 'DefaultFortran.cmake'),
                        utils_path + '/DefaultFortran.cmake')
