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

"""
    Utils
    =====
     Utils manage function needed by converter
"""

import os
import glob
import re
import time
import colorama
import ntpath


def init_colorama():
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

    def init_context_current_setting(self, context):
        """
        Define settings of converter.

        :param context: converter context
        :type context: Context
        """

        conf = None
        arch = None

        if context.current_setting is not None:
            conf_arch = context.current_setting.split('|')
            conf = conf_arch[0]
            arch = conf_arch[1]
            context.supported_architectures.add(arch)

        context.settings[context.current_setting] = {
            'defines': [],
            'conf': conf,
            'arch': arch,
            'target_name': [],
            'target_type': '',
            'out_dir': [],
            'inc_dirs': [],
            'inc_dirs_list': [],
            'add_lib_deps': [],
            'target_link_dirs': [],
            'import_library_path': [],
            'import_library_name': [],
            'pre_build_events': [],
            'pre_link_events': [],
            'post_build_events': [],
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
        message(context, '{0} file is absent at filesystem. Ignoring but check it!!'
                .format(name_to_search), 'warn')
        return ''

    search_list.remove(real_name)
    return real_name


def is_settings_has_data(sln_configurations_map, settings, settings_key, arch=None, conf=None):
    for sln_setting in settings:
        if sln_setting not in sln_configurations_map:
            continue
        mapped_setting_name = sln_configurations_map[sln_setting]
        mapped_setting = settings[mapped_setting_name]
        if settings_key in mapped_setting:
            if arch and mapped_setting['arch'] != arch:
                continue
            if conf and mapped_setting['conf'] != conf:
                continue
            if mapped_setting[settings_key]:
                return True
    return False


def write_property_of_setting_f(cmake_file,
                                indent,
                                config_condition_expr,
                                property_value,
                                width,
                                **kwargs):
    separator = kwargs['separator']
    quotes = '"' if kwargs['quotes'] else ''

    indent = indent + '    '
    config_width = width + 3 + len(quotes)  # for '$<' and ':'

    property_value_str = get_str_value_from_property_value(property_value, separator)
    property_list_str = property_value_str.split('\n')

    if len(property_list_str) == 1:
        cmake_file.write('{0}{1:>{width}}{2}>{3}\n'
                         .format(indent, quotes + '$<' + config_condition_expr + ':',
                                 separator.join(property_value),
                                 quotes, width=config_width))
        return

    first = True
    prop_indent = indent + ' ' * (config_width - len(quotes))
    for prop in property_list_str:
        if first:
            cmake_file.write('{0}{1:>{width}}{3}{2}\n'
                             .format(indent, quotes + '$<' + config_condition_expr + ':',
                                     quotes, prop, width=config_width))
            first = False
            continue
        cmake_file.write(
            '{0}{1:>{width}}\n'.format(prop_indent, quotes + prop + quotes, width=config_width)
        )

    cmake_file.write('{0}{1}\n'
                     .format(prop_indent, quotes + '>' + quotes
                             , width=config_width))


def get_str_value_from_property_value(property_value, separator):
    if isinstance(property_value, list):
        return separator.join(property_value)

    raise str('property value must be a list')


def write_selected_sln_setting(cmake_file,
                               settings,
                               sln_setting_2_project_setting,
                               sln_setting,
                               property_name,
                               has_property_value,
                               begin_text,
                               indent,
                               command_indent,
                               sln_conf,
                               config_expressions,
                               write_setting_property_func,
                               max_config_condition_width,
                               separator,
                               in_quotes,
                               ):

    mapped_setting = settings[sln_setting_2_project_setting[sln_setting]]
    if property_name in mapped_setting:
        if mapped_setting[property_name]:
            if not has_property_value:
                begin_text = begin_text.replace('\n', '\n' + indent + command_indent)
                if begin_text:
                    cmake_file.write('{0}{1}\n'.format(indent + command_indent, begin_text))
                has_property_value = True

            config_condition_expr = None
            if sln_conf is not None:
                config_condition_expr = '$<CONFIG:{0}>'.format(sln_conf)
                config_expressions.append(config_condition_expr)
            write_setting_property_func(cmake_file,
                                        indent + command_indent,
                                        config_condition_expr,
                                        mapped_setting[property_name],
                                        max_config_condition_width,
                                        separator=separator,
                                        quotes=in_quotes)
    return has_property_value


# pylint: disable=R0914
# pylint: disable=R0913


def write_property_of_settings(cmake_file, settings, sln_setting_2_project_setting,
                               indent='',
                               default=None,
                               separator=';',
                               in_quotes=False,
                               write_setting_property_func=write_property_of_setting_f,
                               ignore_global=False,
                               **kwargs):
    """
    Write property of given settings.

    :param cmake_file: CMakeLists.txt IO wrapper
    :type cmake_file: _io.TextIOWrapper
    :param settings: global settings
    :type settings: dict
    :param sln_setting_2_project_setting: solution settings attached to project
    :type sln_setting_2_project_setting: dict
    :param indent: indent to use when writing
    :type indent: str
    :param default: default text to add
    :type default: None | str
    :param separator: separator for property list
    :type separator: ; | str
    :param in_quotes: Enclose configuration settings in quotes
    :type in_quotes: False | bool
    :param write_setting_property_func: function for writing property for setting
    :type write_setting_property_func: write_property_of_setting | lambda
    :param ignore_global: ignore global setting
    :type ignore_global: bool
    :param kwargs: begin of text
    :type kwargs: str
    """

    begin_text = kwargs['begin_text']
    end_text = kwargs['end_text']
    property_name = kwargs['property_name']

    has_property_value = False

    if not ignore_global:
        write_selected_sln_setting(
            cmake_file, settings, sln_setting_2_project_setting, None, property_name,
            has_property_value, begin_text,
            indent,
            '',
            None,
            [],
            write_setting_property_func,
            0,
            separator,
            in_quotes
        )

    max_config_condition_width = 0
    settings_of_arch = {}
    for sln_setting in sln_setting_2_project_setting:
        if sln_setting is None:
            continue
        conf = sln_setting.split('|')[0]
        arch = sln_setting.split('|')[1]
        length = len('$<CONFIG:{0}>'.format(conf))
        if length > max_config_condition_width:
            max_config_condition_width = length
        if arch not in settings_of_arch:
            settings_of_arch[arch] = {}
        settings_of_arch[arch][sln_setting] = sln_setting

    first_arch = True
    for arch in settings_of_arch:
        has_data = is_settings_has_data(sln_setting_2_project_setting, settings, property_name,
                                        arch)
        if not has_data:
            continue

        if first_arch:
            cmake_file.write('{0}if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'
                             .format(indent, arch))
        else:
            cmake_file.write('{0}elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'
                             .format(indent, arch))
        first_arch = False
        has_property_value = False
        command_indent = '    '
        config_expressions = []
        for sln_setting in settings_of_arch[arch]:
            sln_conf = sln_setting.split('|')[0]
            if sln_setting_2_project_setting[sln_setting] not in settings:
                continue

            has_property_value = write_selected_sln_setting(
                cmake_file, settings, sln_setting_2_project_setting, sln_setting, property_name,
                has_property_value, begin_text,
                indent,
                command_indent,
                sln_conf,
                config_expressions,
                write_setting_property_func,
                max_config_condition_width,
                separator,
                in_quotes
            )
        if has_property_value:
            if default:
                cmake_file.write('{0}    $<$<NOT:$<OR:{1}>>:{2}>\n'
                                 .format(indent + command_indent, ','.join(config_expressions),
                                         default))
            end_text = end_text.replace('\n', '\n' + indent + command_indent)
            if end_text:
                cmake_file.write('{0}{1}\n'.format(indent + command_indent, end_text))
    if not first_arch:
        cmake_file.write('{0}endif()\n'.format(indent))

    return not first_arch

# pylint: enable=R0914
# pylint: enable=R0913


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
    variables_to_replace = {
        '$(SolutionDir)': '${CMAKE_SOURCE_DIR}/',
        '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}/',
        '$(OutDir)': '${OUT_DIR}',
        '$(TargetPath)': '$<TARGET_FILE:${PROJECT_NAME}>',
    }
    for var in variables_to_replace:
        if var in output:
            output = output.replace(var, '$<SHELL_PATH:{0}>'.format(variables_to_replace[var]))

    return output


def replace_vs_var_with_cmake_var(context, var):
    variables_to_replace = {
        '$(SolutionDir)': '${CMAKE_SOURCE_DIR}\\',
        '$(Platform)': '${CMAKE_VS_PLATFORM_NAME}',
        '$(PlatformName)': '${CMAKE_VS_PLATFORM_NAME}',
        '$(Configuration)': '$<CONFIG>',
        '$(ConfigurationName)': '$<CONFIG>',
        '$(ProjectDir)': '${CMAKE_CURRENT_SOURCE_DIR}\\',
        '$(ProjectName)': '${PROJECT_NAME}',
        '$(OutDir)': '${OUT_DIR}',
        '$(OUTDIR)': '${OUT_DIR}',
        '$(TargetDir)': '${OUT_DIR}',
        '$(TargetName)': '${TARGET_NAME}',
        '$(TargetFileName)': '$<TARGET_FILE_NAME:${TARGET_NAME}>',
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

    name = set_unix_slash(name)
    dirs = name.split('/')
    # disk letter
    test_name = [dirs[0]]
    for d in dirs[1:]:
        test_name += ["%s[%s]" % (d[:-1], d[-1])]
    res = glob.glob('/'.join(test_name))
    if not res:
        # File not found
        message(context, 'file or path "{0}" not found.'.format(name), 'warn')
        return None

    return res[0]


def normalize_path(context, working_path, path_to_normalize, remove_relative=True):
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
    :return: normalized path
    :rtype: str
    """

    joined_path = os.path.join(working_path, ntpath.normpath(path_to_normalize.strip()))
    normal_path = os.path.normpath(joined_path)
    actual_path_name = get_actual_filename(context, normal_path)
    if actual_path_name is None:
        actual_path_name = normal_path
    normal_path = set_unix_slash(os.path.relpath(actual_path_name, working_path))
    normal_path = check_for_relative_in_path(context, normal_path, remove_relative)

    return normal_path


def prepare_build_event_cmd_line_for_cmake(context, build_event):
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
    if context.project_number:
        message_begin = message_begin + '{0}> '.format(context.project_number)

    if context.current_setting:
        text = '{0} : {1}'.format(context.current_setting, text)

    if status == 'error':
        print(message_begin + 'ERR  : ' + FAIL + text + ENDC)
    elif 'warn' in status:
        if status == 'warn':
            status += '1'
        message_warning_level = int(status[-1])
        if message_warning_level <= context.warn_level:
            print(message_begin + 'WARN : ' + WARN + text + ENDC)
    elif status == 'ok':
        print(message_begin + 'OK   : ' + OK + text + ENDC)
    elif status == 'done':
        print(message_begin + DONE + text + ENDC)
    else:
        if context.verbose:
            print(message_begin + 'INFO : ' + text)


def get_comment(text):
    line_length = 80
    title_line = ''

    for _ in range(0, line_length):
        title_line = '{0}{1}'.format(title_line, '#')

    comment = title_line + '\n'
    comment += '# {0}\n'.format(text)
    comment += title_line + '\n'
    return comment


def write_comment(cmake_file, text):
    """
    Write formated comment in given file wrapper

    :param text: text in middle of title
    :type text: str
    :param cmake_file: CMakeLists.txt IO wrapper
    :type cmake_file: _io.TextIOWrapper
    """

    cmake_file.write(get_comment(text))


def write_arch_types(cmake):
    write_comment(
        cmake,
        'Set target arch type if empty. Visual studio solution generator provides it.'
    )
    cmake.write('if(NOT CMAKE_VS_PLATFORM_NAME)\n')
    cmake.write('    set(CMAKE_VS_PLATFORM_NAME "x64")\n')
    cmake.write('endif()\n')
    cmake.write('message(\"${CMAKE_VS_PLATFORM_NAME} architecture in use\")\n\n')


def write_use_package_stub(cmake):
    write_comment(cmake, 'Nuget packages function stub.')
    cmake.write('function(use_package TARGET PACKAGE VERSION)\n')
    cmake.write('    message(WARNING "No implementation of use_package. Create yours.")\n')
    cmake.write('endfunction()\n\n')
