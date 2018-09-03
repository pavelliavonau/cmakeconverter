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

import re
import os
import copy
import shutil
from multiprocessing import Pool

from .vcxproj.context import VCXContextInitializer
from .vfproj.context import VFContextInitializer
from cmake_converter.data_converter import DataConverter
from cmake_converter.context import ContextInitializer
from cmake_converter.data_files import get_cmake_lists
from cmake_converter.utils import set_unix_slash, message, write_comment


def run_conversion(subdirectory_projects_data):
    for project_data in subdirectory_projects_data:
        project_context = project_data['project_context']
        name = project_context.project_number
        message(project_context, '------ Starting {} -------'.format(name), '')
        convert_project(
            project_context,
            project_data['project_abs'],
            project_data['subdirectory'],
        )
        message(project_context, '------ Exiting  {} -------'.format(name), '')

    result = []
    for project_data in subdirectory_projects_data:
        project_context = project_data['project_context']
        result.append(
            {
                'cmake': project_context.cmake,
                'project_name': project_context.project_name,
                'solution_languages': project_context.solution_languages
            }
        )
    return result


def parse_solution(sln_text):
    """
    Parse given solution

    :param sln_text: full solution text
    :type sln_text: str
    :return: data from solution
    :rtype: dict
    """

    solution_data = {}
    projects_data = {}
    solution_folders = {}
    p = re.compile(
        r'(Project.*\s=\s\"(.*)\",\s\"(.*)\",.*({.*\})(?:.|\n)*?EndProject(?!Section))'
    )

    parsed_data = p.findall(sln_text)
    for project_data_match in parsed_data:
        path = project_data_match[2]
        guid = project_data_match[3]

        file_name, ext = os.path.splitext(os.path.basename(path))

        if 'proj' not in ext:
            solution_folders[guid] = path
            continue

        project = dict()
        project['name'] = project_data_match[1]
        project['path'] = path
        if 'ProjectDependencies' in project_data_match[0]:
            project['sln_deps'] = []
            dependencies_section = re.compile(
                r'ProjectSection\(ProjectDependencies\) = postProject(?:.|\n)*?EndProjectSection'
            )
            dep_data = dependencies_section.findall(project_data_match[0])
            dependencies_guids = re.compile(r'(({.*\}) = ({.*\}))')
            guids_deps_matches = dependencies_guids.findall(dep_data[0])
            for guids_deps_match in guids_deps_matches:
                project['sln_deps'].append(guids_deps_match[2])
        projects_data[guid] = project

    solution_configurations_re = re.compile(
        r'GlobalSection\(SolutionConfigurationPlatforms\) = preSolution((?:.|\n)*?)EndGlobalSection'
    )

    solution_configurations_matches = solution_configurations_re.findall(sln_text)
    solution_data['sln_configurations'] = []
    sln_configuration_re = re.compile(r'([\w|]+) = ([\w|]+)')
    for solution_configuration_match in solution_configurations_matches:
        configurations = sln_configuration_re.findall(solution_configuration_match)
        for configuration in configurations:
            solution_data['sln_configurations'].append(configuration[0])

    projects_configurations_re = re.compile(
        r'GlobalSection\(ProjectConfigurationPlatforms\) = postSolution((?:.|\n)*?)EndGlobalSection'
    )
    projects_configurations_matches = projects_configurations_re.findall(sln_text)
    projects_configuration_re = re.compile(r'({.+\})\.([\w|]+)\.ActiveCfg = ([\w|]+)')
    for projects_configuration_match in projects_configurations_matches:
        configurations = projects_configuration_re.findall(projects_configuration_match)
        for configuration in configurations:
            p = projects_data[configuration[0]]
            if 'sln_configs_2_project_configs' not in p:
                p['sln_configs_2_project_configs'] = {}
            p['sln_configs_2_project_configs'][configuration[1]] = configuration[2]

    nested_projects_re = re.compile(
        r'GlobalSection\(NestedProjects\) = preSolution((?:.|\n)*?)EndGlobalSection'
    )
    solution_folders_map = {}
    nested_projects_matches = nested_projects_re.findall(sln_text)
    solution_dir_link_re = re.compile(r'(\{.+\}) = (\{.+\})')
    for nested_projects_match in nested_projects_matches:
        solution_dir_links = solution_dir_link_re.findall(nested_projects_match)
        for solution_dir_link in solution_dir_links:
            solution_folders_map[solution_dir_link[0]] = solution_dir_link[1]

    set_solution_dirs_to_projects(projects_data, solution_folders_map, solution_folders)

    # replace GUIDs with Project names in dependencies
    for project_guid in projects_data:
        project_data = projects_data[project_guid]
        if 'sln_deps' in project_data:
            target_deps = []
            dependencies_list = project_data['sln_deps']
            for dep_guid in dependencies_list:
                dep = projects_data[dep_guid]
                target_deps.append(dep['name'])
            project_data['sln_deps'] = target_deps
    solution_data['projects_data'] = projects_data

    return solution_data


def set_solution_dirs_to_projects(projects_data, solution_folders_map, solution_folders):
    for project_guid in projects_data:
        project_solution_dir = ''

        if project_guid in solution_folders_map:
            guid = project_guid
            while guid in solution_folders_map:
                if project_solution_dir:
                    project_solution_dir = '/' + project_solution_dir
                project_solution_dir = solution_folders[solution_folders_map[guid]]\
                    + project_solution_dir
                guid = solution_folders_map[guid]

        projects_data[project_guid]['project_solution_dir'] = project_solution_dir


def convert_project(context, xml_project_path, cmake_lists_destination_path):
    """
    Convert a ``vcxproj`` to a ``CMakeLists.txt``

    :param context: input data of user
    :type context: Context
    :param xml_project_path: input xml_proj
    :type xml_project_path: str
    :param cmake_lists_destination_path: Destination folder of CMakeLists.txt
    :type cmake_lists_destination_path: str
    """

    # Initialize Context of DataConverter
    data_converter = None
    if 'vcxproj' in xml_project_path:
        VCXContextInitializer(context, xml_project_path, cmake_lists_destination_path)
        data_converter = DataConverter()
    if 'vfproj' in xml_project_path:
        VFContextInitializer(context, xml_project_path, cmake_lists_destination_path)
        data_converter = DataConverter()
    if data_converter is None:
        message(context, 'Unknown project type at {0}'.format(xml_project_path), 'error')
        return

    data_converter.convert(context)


def set_dependencies_for_project(context, project_data):
    if 'sln_deps' not in project_data:
        return

    context.sln_deps = project_data['sln_deps']


def clean_cmake_lists_file(context, subdirectory, cmake_lists_set):
    cmake_path_to_clean = \
        ContextInitializer.set_cmake_lists_path(context, subdirectory) + '/CMakeLists.txt'
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


def clean_cmake_lists_of_solution(context, solution_path, projects_data):
    if not os.path.exists(os.path.join(solution_path, 'CMake')):
        return  # first run

    message(context, 'Cleaning CMake Scripts', '')
    cmake_lists_set = set()
    for guid in projects_data:
        project_path = projects_data[guid]['path']
        project_path = '/'.join(project_path.split('\\'))
        project_abs = os.path.join(solution_path, project_path)
        subdirectory = os.path.dirname(project_abs)
        clean_cmake_lists_file(context, subdirectory, cmake_lists_set)

    clean_cmake_lists_file(context, solution_path, cmake_lists_set)
    print('\n')


def convert_solution(initial_context, sln_path):
    initial_context.is_converting_solution = True
    sln = open(sln_path, encoding='utf8')
    solution_data = parse_solution(sln.read())
    sln.close()

    solution_path = os.path.dirname(sln_path)
    subdirectories_set = set()
    subdirectories_to_project_name = {}
    projects_data = solution_data['projects_data']
    clean_cmake_lists_of_solution(initial_context, solution_path, projects_data)

    threads_data = {}
    project_number = 0
    for guid in projects_data:
        project_number += 1
        project_context = copy.deepcopy(initial_context)
        project_context.project_number = project_number
        project_path = projects_data[guid]['path']
        project_path = '/'.join(project_path.split('\\'))
        project_abs = os.path.join(solution_path, project_path)
        subdirectory = os.path.dirname(project_abs)
        set_dependencies_for_project(project_context, projects_data[guid])
        project_context.sln_configurations_map = \
            projects_data[guid]['sln_configs_2_project_configs']
        project_context.solution_folder = projects_data[guid]['project_solution_dir']
        if subdirectory not in threads_data:
            threads_data[subdirectory] = []
        threads_data[subdirectory].append({
            'project_context': project_context,
            'project_abs': project_abs,
            'subdirectory': subdirectory}
        )

    threads_data_list = []
    for subdirectory in threads_data:
        threads_data_list.append(threads_data[subdirectory])

    results = []
    if initial_context.jobs > 1:
        pool = Pool(initial_context.jobs)
        results = pool.map(run_conversion, threads_data_list)
    else:   # do in main thread
        i = 0
        for threads_data in threads_data_list:
            results.append(run_conversion(threads_data))
            i += 1

    for directory_results in results:
        for project_result in directory_results:
            subdirectory = os.path.relpath(project_result['cmake'], solution_path)
            if subdirectory != '.':
                subdirectories_set.add(subdirectory)
            subdirectories_to_project_name[subdirectory] = project_result['project_name']
            initial_context.solution_languages.update(project_result['solution_languages'])

    if initial_context.dry:
        return

    sln_cmake = get_cmake_lists(initial_context, solution_path, 'r')
    sln_cmake_projects_text = ''
    if sln_cmake is not None:
        sln_cmake_projects_text = sln_cmake.read()
        sln_cmake.close()

    sln_cmake = get_cmake_lists(initial_context, solution_path)
    DataConverter.add_cmake_version_required(sln_cmake)
    sln_cmake.write(
        'project({0})\n\n'.format(os.path.splitext(os.path.basename(sln_path))[0])
    )
    write_comment(
        sln_cmake,
        'Set target arch type if empty. Visual studio solution generator provides it.'
    )
    sln_cmake.write('if(NOT CMAKE_VS_PLATFORM_NAME)\n')
    sln_cmake.write('    set(CMAKE_VS_PLATFORM_NAME "x64")\n')
    sln_cmake.write('endif()\n')
    sln_cmake.write('message(\"${CMAKE_VS_PLATFORM_NAME} architecture in use\")\n\n')

    # TODO: try to write configuration types for each project locally due possible difference.
    write_comment(sln_cmake, 'Global configuration types')
    sln_cmake.write('set(CMAKE_CONFIGURATION_TYPES\n')
    configuration_types_set = set()
    for config in solution_data['sln_configurations']:
        configuration_types_set.add(config.split('|')[0])
    configuration_types_list = list(configuration_types_set)
    configuration_types_list.sort(key=str.lower)
    for configuration_type in configuration_types_list:
        sln_cmake.write('    \"{0}\"\n'.format(configuration_type))
    sln_cmake.write('    CACHE TYPE INTERNAL FORCE\n)\n\n')

    write_comment(sln_cmake, 'Global compiler options')
    sln_cmake.write('if(MSVC)\n')
    sln_cmake.write('    # remove default flags provided with CMake for MSVC\n')
    solution_languages = list(initial_context.solution_languages)
    solution_languages.sort(key=str.lower)
    for lang in solution_languages:
        sln_cmake.write('    set(CMAKE_{0}_FLAGS "")\n'.format(lang))
        for configuration_type in configuration_types_list:
            sln_cmake.write('    set(CMAKE_{0}_FLAGS_{1} "")\n'
                            .format(lang, configuration_type.upper()))
    sln_cmake.write('endif()\n\n')

    write_comment(sln_cmake, 'Global linker options')
    sln_cmake.write('if(MSVC)\n')
    sln_cmake.write('    # remove default flags provided with CMake for MSVC\n')
    sln_cmake.write('    set(CMAKE_EXE_LINKER_FLAGS "")\n')
    sln_cmake.write('    set(CMAKE_MODULE_LINKER_FLAGS "")\n')
    sln_cmake.write('    set(CMAKE_SHARED_LINKER_FLAGS "")\n')
    sln_cmake.write('    set(CMAKE_STATIC_LINKER_FLAGS "")\n')
    for configuration_type in configuration_types_list:
        ct_upper = configuration_type.upper()
        sln_cmake.write(
            '    set(CMAKE_EXE_LINKER_FLAGS_{0} \"${{CMAKE_EXE_LINKER_FLAGS}}\")\n'
            .format(ct_upper))
        sln_cmake.write(
            '    set(CMAKE_MODULE_LINKER_FLAGS_{0} \"${{CMAKE_MODULE_LINKER_FLAGS}}\")\n'
            .format(ct_upper))
        sln_cmake.write(
            '    set(CMAKE_SHARED_LINKER_FLAGS_{0} \"${{CMAKE_SHARED_LINKER_FLAGS}}\")\n'
            .format(ct_upper))
        sln_cmake.write(
            '    set(CMAKE_STATIC_LINKER_FLAGS_{0} \"${{CMAKE_STATIC_LINKER_FLAGS}}\")\n'
            .format(ct_upper))
    sln_cmake.write('endif()\n\n')

    write_comment(sln_cmake, 'Nuget packages function stub.')

    sln_cmake.write('function(use_package TARGET PACKAGE VERSION)\n')
    sln_cmake.write('    message(WARNING "No implementation of use_package. Create yours.")\n')
    sln_cmake.write('endfunction()\n\n')

    write_comment(sln_cmake, 'Common utils')
    sln_cmake.write('include(CMake/Utils.cmake)\n\n')
    utils_path = os.path.join(solution_path, 'CMake')
    if not os.path.exists(utils_path):
        os.makedirs(utils_path)
    utils_src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../utils.cmake')
    shutil.copyfile(utils_src_path, utils_path + '/Utils.cmake')

    write_comment(sln_cmake, 'Additional Global Settings(add specific info there)')
    sln_cmake.write('include(CMake/GlobalSettingsInclude.cmake OPTIONAL)\n\n')

    write_comment(sln_cmake, 'Use solution folders feature')
    sln_cmake.write('set_property(GLOBAL PROPERTY USE_FOLDERS ON)\n\n')

    write_comment(sln_cmake, 'Sub-projects')

    subdirectories = list(subdirectories_set)
    subdirectories.sort(key=str.lower)
    for subdirectory in subdirectories:
        binary_dir = ''
        if '.' in subdirectory[:1]:
            binary_dir = ' ${{CMAKE_BINARY_DIR}}/{0}'.format(
                subdirectories_to_project_name[subdirectory])
        sln_cmake.write('add_subdirectory({0}{1})\n'.format(
            set_unix_slash(subdirectory), binary_dir))
    sln_cmake.write('\n')

    if sln_cmake_projects_text != '':
        sln_cmake.write('\n' * 26)
        sln_cmake.write(sln_cmake_projects_text)

    sln_cmake.close()

    message(initial_context, 'Conversion of solution finished', 'done')
