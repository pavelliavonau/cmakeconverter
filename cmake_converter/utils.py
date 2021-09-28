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
    Utils
    =====
     Utils manage function needed by converter
"""

import os
import glob
import re
import time
import ntpath
import sysconfig


import colorama


def init_colorama():
    """ Initialization of colorful console output """
    if 'PYCHARM_HOSTED' in os.environ:
        convert = False  # in PyCharm, we should disable convert
        strip = False
        print("Hi! You are using PyCharm")
    else:
        convert = None
        strip = None
    colorama.init(convert=convert, strip=strip)


init_colorama()

DONE = colorama.Fore.GREEN + colorama.Style.BRIGHT
OK = colorama.Fore.CYAN + colorama.Style.BRIGHT
WARN = colorama.Fore.YELLOW + colorama.Style.BRIGHT
FAIL = colorama.Fore.RED + colorama.Style.BRIGHT
ENDC = colorama.Fore.RESET + colorama.Style.RESET_ALL


class Utils:
    """ Basic Class for holding util functions needed by converter """
    @staticmethod
    def lists_of_settings_to_merge():
        """ Lists of keys of settings at context that will be merged """
        return [
            'defines',
            'inc_dirs',
            'target_link_dirs',
            'add_lib_deps',
            'PDB_OUTPUT_DIRECTORY',
            'PDB_NAME',
            'INTERPROCEDURAL_OPTIMIZATION'
        ]

    def init_context_current_setting(self, context):
        """
        Define settings of converter.

        :param context: converter context
        :type context: Context
        """

        conf = context.current_setting[0]
        arch = context.current_setting[1]

        setting = (conf, arch)
        context.settings[setting] = {
            'conf': conf,
            'arch': arch,
            'TARGET_NAME': [],
            'target_type': '',
            'OUTPUT_DIRECTORY': [],
            'inc_dirs_list': [],
            'ARCHIVE_OUTPUT_DIRECTORY': [],
            'ARCHIVE_OUTPUT_NAME': [],
            'VS_GLOBAL_KEYWORD': [],
            'INTERPROCEDURAL_OPTIMIZATION': [],
            'pre_build_events': {},
            'pre_link_events': {},
            'post_build_events': {},
            'custom_build_events': {},
        }


def take_name_from_list_case_ignore(context, search_list, name_to_search):
    """
    Return real name of name to search

    :param context: the context of converter
    :type context: Context
    :param search_list: list to makje research
    :type search_list: list
    :param name_to_search: name tosearch in list
    :type name_to_search: str
    :return: real name
    :rtype: str
    """

    real_name = ''
    for item in search_list:
        if item.lower() == name_to_search.lower():
            real_name = item
            break

    if real_name == '':
        message(context, '{} is absent.'.format(name_to_search), 'warn')
        return ''

    search_list.remove(real_name)
    return real_name


def is_settings_has_data(sln_configurations_map, settings, settings_key, sln_arch=None, conf=None):
    """ Checker of available settings in context """
    if sln_arch:
        mapped_archs = get_mapped_architectures(sln_configurations_map, sln_arch)

    for sln_setting in sln_configurations_map:
        mapped_setting_key = sln_configurations_map[sln_setting]
        if mapped_setting_key not in settings:
            continue
        mapped_setting = settings[mapped_setting_key]
        if sln_arch and (mapped_setting_key[1] not in mapped_archs):
            continue
        if conf and (mapped_setting_key[0] != conf):
            continue

        if settings_key in mapped_setting:
            if mapped_setting[settings_key]:
                return True
    return False


def get_mapped_architectures(sln_setting_2_project_setting, arch):
    """ Get all projects architectures that mapped onto given solution one """
    archs = set()
    for setting in sln_setting_2_project_setting:
        if setting[1] == arch:
            archs.add(sln_setting_2_project_setting[setting][1])
    return archs


def get_global_project_name_from_vcxproj_file(vcxproj):
    """
    Return global project name from ".vcxproj" file

    :param vcxproj: vcxproj data
    :type vcxproj: dict
    :return: project name
    :rtype: str
    """

    project_name_node = vcxproj['tree'].xpath('//ns:ProjectName', namespaces=vcxproj['ns'])
    project_name = None
    if project_name_node:
        project_name_value = project_name_node[0]
        if project_name_value.text:
            project_name = project_name_value.text

    return project_name


def set_unix_slash(win_path):
    """
    Set windows path to unix style path

    :param win_path: windows style path
    :type win_path: str
    :return: unix style path
    :rtype: str
    """
    unix_path = win_path.strip().replace('\\', '/')

    return unix_path


def set_native_slash(raw_path):
    """
    Set native slash

    :param raw_path: any style path
    :type raw_path: str
    :return: unix style path
    :rtype: str
    """

    to_replace = ''
    if os.path.sep == '\\':
        to_replace = '/'
    if os.path.sep == '/':
        to_replace = '\\'

    return raw_path.strip().replace(to_replace, os.path.sep)


def get_mount_point(path):
    """ Returns mount point of given path """
    folders = path.split(os.path.sep)
    mount_point = ''
    for folder in folders:
        if not folder:
            mount_point += '/'
            continue
        mount_point += '{}/'.format(folder)
        if os.path.ismount(mount_point):
            break
    return mount_point


def check_for_relative_in_path(context, path, remove_relative=True):
    """
    Return path by adding CMake variable or current path prefix, to remove relative

    :param context: the context of converter
    :type context: Context
    :param path: original path
    :type path: str
    :param remove_relative: flag
    :type remove_relative: bool
    :return: formatted path without relative
    :rtype: str
    """

    path_has_drive_path = path[1:2] == ':'
    if path_has_drive_path:
        message(context, 'Found absolute path : {}'.format(path), 'warn')
        return path

    path_starts_with_variable = path[0:1] == '$'
    if not path_starts_with_variable and remove_relative:
        # add current directory for relative path (CMP0021)
        path = '${CMAKE_CURRENT_SOURCE_DIR}/' + path

    return path


def make_os_specific_shell_path(output):
    """ Tries to make path readable with CMake """
    variables_to_replace = {
        '$(SolutionDir)': '${CMAKE_SOURCE_DIR}/',
        '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}/',
        '$(OutDir)': '${OUTPUT_DIRECTORY}',
        '$(TargetPath)': '$<TARGET_FILE:${PROJECT_NAME}>',
    }
    for sln_var, cmake_var in variables_to_replace.items():
        if sln_var in output:
            output = output.replace(sln_var, '$<SHELL_PATH:{}>'.format(cmake_var))

    return output


def resolve_path_variables_of_vs(context, path_with_vars):
    """ Evaluates paths with visual studio variables """
    path_with_vars = path_with_vars.replace('$(ProjectDir)', './')
    path_with_vars = path_with_vars.replace('$(SolutionDir)', context.solution_path + '/')
    return path_with_vars


def get_dir_name_with_vars(context, path):
    """ Tries to split directory and filename from given path """
    del context
    dirname = os.path.dirname(path)
    file_name = os.path.basename(path)
    if not dirname:
        dirname_pattern = re.compile(r'(\$\{.*dir[^\}]*\})', re.IGNORECASE)
        m = dirname_pattern.match(path)
        if m:
            dirname = m.group(0)

        file_name = path.replace(dirname, '')

    file_name, _ = os.path.splitext(os.path.basename(file_name))

    return dirname, file_name


def replace_vs_var_with_cmake_var(context, var):
    """ Translate Visual studio variable into CMake variable """
    variables_to_replace = {
        '$(SolutionDir)': '${CMAKE_SOURCE_DIR}\\',
        '$(Platform)': '${CMAKE_VS_PLATFORM_NAME}',
        '$(PlatformName)': '${CMAKE_VS_PLATFORM_NAME}',
        '$(Configuration)': '$<CONFIG>',
        '$(ConfigurationName)': '$<CONFIG>',
        '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}\\',
        '$(ProjectName)': '${PROJECT_NAME}',
        '$(RootNamespace)': '${ROOT_NAMESPACE}',
        '$(OutDir)': '${OUTPUT_DIRECTORY}',
        '$(OUTDIR)': '${OUTPUT_DIRECTORY}',
        '$(IntDir)': '${CMAKE_CURRENT_BINARY_DIR}\\${CMAKE_CFG_INTDIR}\\',
        '$(INTDIR)': '${CMAKE_CURRENT_BINARY_DIR}\\${CMAKE_CFG_INTDIR}\\',
        '$(TargetDir)': '${OUTPUT_DIRECTORY}',
        '$(TargetName)': '${TARGET_NAME}',
        '$(TargetFileName)': '$<TARGET_FILE_NAME:${PROJECT_NAME}>',
        '$(TargetPath)': '$<TARGET_FILE:${PROJECT_NAME}>',
    }
    if var in variables_to_replace:
        return variables_to_replace[var]

    var_name = var[2:-1]
    cmake_env_var = '$ENV{{{}}}'.format(var_name)
    if var_name not in os.environ:
        message(context, 'Unknown variable: {}, trying {}'.format(var, cmake_env_var), 'warn')
    return cmake_env_var


def replace_vs_vars_with_cmake_vars(context, output):
    """ Translates variables at given string to corresponding CMake ones """
    var_ex = re.compile(r'(\$\(.*?\))')

    vars_list = var_ex.findall(output)
    for var in vars_list:
        replace_with = replace_vs_var_with_cmake_var(context, var)
        output = output.replace(var, replace_with)

    return output


def cleaning_output(context, output):
    """
    Clean Output string by remove VS Project Variables

    :param context: the context of converter
    :type context: Context
    :param output: Output to clean
    :type output: str
    :return: clean output
    :rtype: str
    """

    output = replace_vs_vars_with_cmake_vars(context, output)

    output = set_unix_slash(output)

    return output


def insensitive_glob(path):
    """ Searches given path case insensitive """
    drive, path = os.path.splitdrive(path)

    platform = sysconfig.get_platform()
    if 'msys' in platform or 'mingw' in platform:
        drive = path[:2]
        path = path[2:]

    def either(c):
        return '[{}{}]'.format(c.lower(), c.upper()) if c.isalpha() else c
    pattern = drive + ''.join(map(either, path))
    return glob.glob(pattern)


def get_actual_filename(context, name):
    """
    Return actual filename from given name if file iis found, else return None

    :param context: the context of converter
    :type context: Context
    :param name: name of file
    :type name: str
    :return: None | str
    :rtype: None | str
    """

    res = insensitive_glob(name)
    if not res:
        # File not found
        message(context, 'file or path "{}" not found.'.format(name), 'warn')
        return None

    return res[0]


def normalize_path(context, working_path, path_to_normalize, remove_relative=True, unix_slash=True):
    """
    Normalize path from working path

    :param context: the context of converter
    :type context: Context
    :param working_path: current working path
    :type working_path: str
    :param path_to_normalize: path to be normalized
    :type path_to_normalize: str
    :param remove_relative: remove relative from path flag
    :type remove_relative: bool
    :param unix_slash: apply UNIX slash
    :type unix_slash: bool
    :return: normalized path
    :rtype: str
    """

    joined_path = set_native_slash(
        os.path.join(working_path, ntpath.normpath(path_to_normalize.strip()))
    )
    normal_path = os.path.normpath(joined_path)
    actual_path_name = get_actual_filename(context, normal_path)
    if actual_path_name is None:
        message(
            context,
            'getting actual filesystem name failed : "{}"'.format(normal_path),
            'warn1'
        )
        actual_path_name = normal_path
    normal_path = os.path.relpath(actual_path_name, working_path)
    if unix_slash:
        normal_path = set_unix_slash(normal_path)
    normal_path = check_for_relative_in_path(context, normal_path, remove_relative)

    return normal_path


def prepare_build_event_cmd_line_for_cmake(context, build_event):
    """ Tries to fit build event command to be compliant CMake language """
    cmake_build_event = make_os_specific_shell_path(build_event)
    cmake_build_event = replace_vs_vars_with_cmake_vars(context, cmake_build_event)
    cmake_build_event = cmake_build_event.replace('\\', '\\\\')
    return cmake_build_event


def message(context, text, status):  # pragma: no cover
    """
    Displays a message while the script is running

    :param context: the context of converter
    :type context: Context
    :param text: content of the message
    :type text: str
    :param status: level of the message (change color)
    :type status: str
    """

    current_time = time.time()
    delta_time = current_time - context.time0
    dt = '{0:f} '.format(delta_time)

    message_begin = dt
    if context.target_number:
        message_begin = message_begin + '{}> '.format(context.target_number)

    if None not in context.current_setting:
        text = '{} : {}'.format(context.current_setting, text)

    if context.current_node is not None and status:
        text = '{}({}): {}'.format(context.current_node.base, context.current_node.sourceline, text)

    if status == 'error':
        print(message_begin + 'ERR  : ' + FAIL + text + ENDC)
    elif 'warn' in status:
        if status == 'warn':
            status += '1'
        message_warning_level = int(status[-1])
        if message_warning_level <= context.warn_level:
            print(message_begin + 'WARN L' + status[-1] + ' : ' + WARN + text + ENDC)
            context.warnings_count += 1
    elif status == 'ok':
        print(message_begin + 'OK   : ' + OK + text + ENDC)
    elif status == 'done':
        print(message_begin + DONE + text + ENDC)
    else:
        if context.verbose:
            print(message_begin + 'INFO : ' + text)


def escape_string(context, wrong_chars_regex, input_str):
    """ Removes wrong chars from input string """
    output_str = re.sub(wrong_chars_regex, '', input_str)

    if input_str != output_str:
        message(
            context,
            'string from solution fixed for CMake "{}" -> "{}"'.format(input_str, output_str),
            'warn3'
        )
    return output_str


def make_cmake_literal(context, input_str):
    """ Tries to make cmake literal from input string """
    return escape_string(context, r'[^0-9a-zA-Z_./\-+]', input_str)


def make_cmake_configuration(context, sln_configuration):
    """ Tries to make cmake configuration name from sln_configuration """
    sln_conf_arch = sln_configuration.split('|')
    genex_invalid_regex = r'[^A-Za-z0-9_]'
    sln_conf_arch[0] = escape_string(context, genex_invalid_regex, sln_conf_arch[0])
    return "{}|{}".format(*sln_conf_arch)
