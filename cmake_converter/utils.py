#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017:
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
    Utils
    =====
     Utils manage function needed by converter
"""

import sys
import os
import glob
import colorama

path_prefix = ''

DONE = colorama.Fore.GREEN + colorama.Style.BRIGHT
OK = colorama.Fore.CYAN + colorama.Style.BRIGHT
WARN = colorama.Fore.YELLOW + colorama.Style.BRIGHT
FAIL = colorama.Fore.RED + colorama.Style.BRIGHT
ENDC = colorama.Fore.RESET + colorama.Style.RESET_ALL


def take_name_from_list_case_ignore(search_list, name_to_search):
    """
    Return real name of name to search

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
        if '.h' in name_to_search:
            message('{0} header file is absent at filesystem. Ignoring but check it!!\n'
                    .format(name_to_search), 'warn')
            return ''
        message('{0} file is absent at filesystem. Ignoring but check it!!\n'
                .format(name_to_search), 'warn')
    else:
        search_list.remove(real_name)
        return real_name


def get_configuration_type(setting, context):
    """
    Return configuration type from given setting and context

    :param setting: current setting (ReleaseDebug|Win32, ...)
    :type setting: str
    :param context: current context
    :type context: dict
    :return: configuration type
    :rtype: str
    """

    configurationtype = context['vcxproj']['tree'].xpath(
        '{0}/ns:ConfigurationType'.format(context['property_groups'][setting]),
        namespaces=context['vcxproj']['ns'])
    if len(configurationtype) == 0:
        return None

    return configurationtype[0].text


def write_property_of_settings(cmake_file, settings, sln_setting_2_project_setting, begin_text,
                               end_text, property_name, indent='', default=None):
    """
    Write property of given settings. TODO: Add **kwargs to decrease number of parameters

    :param cmake_file: CMakeLists.txt IO wrapper
    :type cmake_file: _io.TextIOWrapper
    :param settings: global settings
    :type settings: dict
    :param sln_setting_2_project_setting: solution settings attached to project
    :type sln_setting_2_project_setting: dict
    :param begin_text: begin of text
    :type begin_text: str
    :param end_text: end of text
    :type end_text: str
    :param property_name: current property name (out_dir, inc_dirs,...)
    :type property_name: str
    :param indent: indent to use when writing
    :type indent: str
    :param default: default text to add
    :type default: None | str
    """

    width = 0
    settings_of_arch = {}
    for sln_setting in sln_setting_2_project_setting:
        conf = sln_setting.split('|')[0]
        arch = sln_setting.split('|')[1]
        length = len('$<$<CONFIG:{0}>'.format(conf))
        if length > width:
            width = length
        if arch not in settings_of_arch:
            settings_of_arch[arch] = {}
        settings_of_arch[arch][sln_setting] = sln_setting

    first_arch = True
    for arch in settings_of_arch:
        if first_arch:
            cmake_file.write('{0}if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'
                             .format(indent, arch))
        else:
            cmake_file.write('{0}elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'
                             .format(indent, arch))
        first_arch = False
        has_property_value = False
        config_expressions = []
        for sln_setting in settings_of_arch[arch]:
            sln_conf = sln_setting.split('|')[0]
            mapped_setting = settings[sln_setting_2_project_setting[sln_setting]]
            if property_name in mapped_setting:
                if mapped_setting[property_name] != '':
                    if not has_property_value:
                        cmake_file.write('{0}    {1}\n'.format(indent, begin_text))
                        has_property_value = True
                    property_value = mapped_setting[property_name]
                    config_expr_begin = '$<CONFIG:{0}>'.format(sln_conf)
                    config_expressions.append(config_expr_begin)
                    cmake_file.write('{0}        {1:>{width}}:{2}>\n'
                                     .format(indent, '$<' + config_expr_begin, property_value,
                                             width=width))
        if has_property_value:
            if default:
                cmake_file.write('{0}        $<$<NOT:$<OR:{1}>>:{2}>\n'
                                 .format(indent, ','.join(config_expressions), default))
            cmake_file.write('{0}    {1}\n'.format(indent, end_text))
    cmake_file.write('{0}else()\n'.format(indent))
    cmake_file.write(
        '{0}    message(WARNING "${{CMAKE_VS_PLATFORM_NAME}} arch is not supported!")\n'
        .format(indent))
    cmake_file.write('{0}endif()\n'.format(indent))


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


def remove_relative_from_path(path):
    """
    Return path by adding CMake variable or current path prefix, to remove relative

    :param path: original path
    :type path: str
    :return: formatted path without relative
    :rtype: str
    """

    if '${' not in path[:2]:
        path = path_prefix + path
    if '.' in path[:1]:
        # add current directory for relative path (CMP0021)
        path = '${CMAKE_CURRENT_SOURCE_DIR}/' + path

    return path


def cleaning_output(output):
    """
    Clean Output string by remove VS Project Variables

    :param output: Output to clean
    :type output: str
    :return: clean output
    :rtype: str
    """

    variables_to_replace = {
        '$(SolutionDir)': '${CMAKE_SOURCE_DIR}/',
        '$(Platform)': '${CMAKE_VS_PLATFORM_NAME}',
        '$(Configuration)': '$<CONFIG>',
        '$(ConfigurationName)': '$<CONFIG>',
        '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}',
        '$(ProjectName)': '${PROJECT_NAME}'
        }

    output = set_unix_slash(output)

    for var in variables_to_replace:
        if var in output:
            output = output.replace(var, variables_to_replace[var])

    output = remove_relative_from_path(output)
    # TODO: Next action is strange. turned off
    # if '%s..' % var in output:
    #     output = output.replace('%s..' % var, '..')

    return output


def get_actual_filename(name):
    """
    Return actual filename from given name if file iis found, else return None

    :param name: name of file
    :type name: str
    :return: None | str
    :rtype: None | str
    """

    dirs = name.split('\\')
    # disk letter
    test_name = [dirs[0].upper()]
    for d in dirs[1:]:
        test_name += ["%s[%s]" % (d[:-1], d[-1])]
    res = glob.glob('\\'.join(test_name))
    if not res:
        # File not found
        message('file or path "{0}" not found.'.format(name), 'warn')
        return None

    return res[0]


def normalize_path(working_path, path_to_normalize):
    """
    Normalize path from working path

    :param working_path: current working path
    :type working_path: str
    :param path_to_normalize: path to be normalized
    :type path_to_normalize: str
    :return: normalized path
    :rtype: str
    """

    joined_path = os.path.normpath(os.path.join(working_path, path_to_normalize.strip()))
    actual_path_name = get_actual_filename(joined_path)
    if actual_path_name is None:
        actual_path_name = joined_path
    normal_path = set_unix_slash(os.path.relpath(actual_path_name, working_path))
    normal_path = remove_relative_from_path(normal_path)

    return normal_path


def message(text, status):  # pragma: no cover
    """
    Displays a message while the script is running

    :param text: content of the message
    :type text: str
    :param status: level of the message (change color)
    :type status: str
    """

    if status == 'error':
        print('ERR  : ' + FAIL + text + ENDC)
    elif status == 'warn':
        print('WARN : ' + WARN + text + ENDC)
    elif status == 'ok':
        print('OK   : ' + OK + text + ENDC)
    elif status == 'done':
        print(DONE + text + ENDC)
    else:
        print('INFO : ' + text)


def get_title(title, text):
    """
    Return formatted title for writing

    :param title: main title text
    :type title: str
    :param text: text related to title
    :type text: str
    :return: formatted title
    :rtype: str
    """

    offset = 60
    text_offset = (offset / 2) - len(title)

    title_sharp = ''
    for _ in range(int(text_offset)):
        title_sharp = '%s#' % title_sharp

    title = '%s %s ' % (title_sharp, title)
    i = len(title)
    while i < offset:
        title = '%s#' % title
        i += 1

    text = '# %s' % text

    i = len(text)
    while i < offset:
        if i < offset - 1:
            text = '%s ' % text
        else:
            text = '%s#' % text
            break
        i += 1

    bottom_text = ''
    for _ in range(offset):
        bottom_text = '%s#' % bottom_text

    return '%s\n%s\n%s\n\n' % (title, text, bottom_text)
