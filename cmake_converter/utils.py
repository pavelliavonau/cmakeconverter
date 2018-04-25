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
     Provides utils functions
"""

import sys
import os


def mkdir(folder):
    """
    Make wanted folder

    :param folder: folder to create
    :type folder: str
    :return: if creation is success or not
    :rtype: bool
    """

    try:
        os.makedirs(folder)
    except FileExistsError:
        pass
    except PermissionError as e:
        print('Can\'t create [%s] directory for cmake !\n%s' % (folder, e))
        sys.exit(1)


def take_name_from_list_case_ignore(search_list, name_to_search):
    """
    """
    real_name = ''
    for item in search_list:
        if item.lower() == name_to_search.lower():
            real_name = item
            break

    if real_name == '':
        if '.h' in name_to_search:
            print('WARNING: {0} header file not  at filesystem. Ignoring but check it!!\n'.format(name_to_search))
            return ''
        raise ValueError('Filename {0} not found at filesystem.'.format(name_to_search))
    else:
        search_list.remove(real_name)
        return real_name


def get_configuration_type(setting, context):
    configurationtype = context['vcxproj']['tree'].xpath(
        '{0}/ns:ConfigurationType'.format(context['property_groups'][setting]),
        namespaces=context['vcxproj']['ns'])
    if len(configurationtype) == 0:
        return None
    return configurationtype[0].text


def write_property_of_settings(cmake_file, settings, begin_text, end_text, property_name, indent='', default=None):
    width = 0
    settings_of_arch = {}
    for setting in settings:
        length = len('$<$<CONFIG:{0}>'.format(settings[setting]['conf']))
        if length > width:
            width = length
        arch = settings[setting]['arch']
        if arch not in settings_of_arch:
            settings_of_arch[arch] = {}
        settings_of_arch[arch][setting] = settings[setting]

    first_arch = True
    for arch in settings_of_arch:
        if first_arch:
            cmake_file.write('{0}if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'.format(indent, arch))
        else:
            cmake_file.write('{0}elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{1}\")\n'.format(indent, arch))
        first_arch = False
        has_property_value = False
        config_expressions = []
        for setting in settings_of_arch[arch]:
            conf = settings[setting]['conf']
            if property_name in settings[setting]:
                if settings[setting][property_name] != '':
                    if not has_property_value:
                        cmake_file.write('{0}    {1}\n'.format(indent, begin_text))
                        has_property_value = True
                    property_value = settings[setting][property_name]
                    config_expr_begin = '$<CONFIG:{0}>'.format(conf)
                    config_expressions.append(config_expr_begin)
                    cmake_file.write('{0}        {1:>{width}}:{2}>\n'.format(indent, '$<' + config_expr_begin,
                                                                             property_value,
                                                                             width=width))
        if has_property_value:
            if default:
                cmake_file.write('{0}        $<$<NOT:$<OR:{1}>>:{2}>\n'.format(indent,
                                                                               ','.join(config_expressions), default))
            cmake_file.write('{0}    {1}\n'.format(indent, end_text))
    cmake_file.write('{0}else()\n'.format(indent))
    cmake_file.write('{0}    message(WARNING "${{CMAKE_VS_PLATFORM_NAME}} arch is not supported!")\n'.format(indent))
    cmake_file.write('{0}endif()\n'.format(indent))


def get_global_project_name_from_vcxproj_file(vcxproj):
    project_name_node = vcxproj['tree'].xpath('//ns:ProjectName', namespaces=vcxproj['ns'])
    project_name = None
    if project_name_node:
        project_name_value = project_name_node[0]
        if project_name_value.text:
            project_name = project_name_value.text
    return project_name
