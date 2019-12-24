#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019:
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
    Data Files
    ==========
     Manage the **VS Project** data and creation of **CMakeLists.txt** file
"""

import os
import sys
from lxml import etree

from cmake_converter.utils import message, get_actual_filename, set_unix_slash


def search_file_path(context, xml_file):
    """ Util function for checking file in path. """
    xml_file = set_unix_slash(xml_file)

    found_xml_file = get_actual_filename(context, xml_file)

    if found_xml_file is None:
        message(
            context,
            '{} file not exists. '.format(xml_file),
            'error'
        )
        return None

    if found_xml_file != xml_file:
        message(
            context,
            'file reference probably has wrong case {}'.format(xml_file),
            'warn4'
        )

    return found_xml_file


def get_vcxproj_data(context, vs_project):
    """
    Return xml data from "vcxproj" file

    :param context: the context of converter
    :type context: Context
    :param vs_project: the vcxproj file
    :type vs_project: str
    :return: dict with VS Project data
    :rtype: dict
    """

    vcxproj = {}
    vs_project = search_file_path(context, vs_project)
    if vs_project is None:
        return None

    try:
        tree = etree.parse(vs_project)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        vcxproj['tree'] = tree
        vcxproj['ns'] = ns
        assert 'http://schemas.microsoft.com' in ns['ns']
    except AssertionError:  # pragma: no cover
        message(
            context,
            '{} file cannot be import, because this file does not seem to comply with'
            ' Microsoft xml data !'.format(vs_project),
            'error'
        )
        sys.exit(1)
    except (OSError, IOError):  # pragma: no cover
        message(
            context,
            '{} file cannot be import. '
            'Please, verify you have rights to this directory or file exists !'.format(vs_project),
            'error'
        )
        sys.exit(1)
    except etree.XMLSyntaxError:  # pragma: no cover
        message(
            context,
            'File {} is not a ".vcxproj" file or XML is broken !'.format(vs_project),
            'error'
        )
        sys.exit(1)

    return vcxproj


def get_xml_data(context, xml_file):
    """
    Return xml data from "xml" file

    :param context: the context of converter
    :type context: Context
    :param xml_file: the xml file
    :type xml_file: str
    :return: dict with VS Project data
    :rtype: dict
    """

    xml = {}
    xml_file = search_file_path(context, xml_file)
    if xml_file is None:
        return None

    try:
        tree = etree.parse(xml_file)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        xml['tree'] = tree
        xml['ns'] = ns
        # assert 'http://schemas.microsoft.com' in ns['ns']
    except AssertionError:  # pragma: no cover
        message(
            context,
            '.xml file {} cannot be import, because this file does not seem to comply with'
            ' Microsoft xml data !'.format(xml_file),
            'error'
        )
        sys.exit(1)
    except (OSError, IOError):  # pragma: no cover
        message(
            context,
            '{} file cannot be import. '
            'Please, verify you have rights to this directory or file exists !'.format(xml_file),
            'error'
        )
        sys.exit(1)
    except etree.XMLSyntaxError:  # pragma: no cover
        message(
            context,
            'File {} is not a ".xml" file or XML is broken !'.format(xml_file),
            'error'
        )
        sys.exit(1)

    return xml


def get_propertygroup(target_platform, attributes=''):
    """
    Return "property_groups" value for wanted platform and target

    :param target_platform: wanted target: debug | release
    :type target_platform: tuple[str,str]
    :param attributes: attributes to add to namespace
    :type attributes: str
    :return: "property_groups" value
    :rtype: str
    """

    prop = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'{}\'"{}]'.format(
            '|'.join(target_platform), attributes)

    return prop


def get_definitiongroup(target_platform):
    """
    Return ItemDefinitionGroup namespace depends on platform and target

    :param target_platform: wanted target: debug | release
    :type target_platform: tuple[str,str]
    :return: wanted ItemDefinitionGroup namespace
    :rtype: str
    """

    item = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'{}\'"]'.format('|'.join(target_platform))

    return item


def get_cmake_lists(context, cmake_path=None, open_type='w'):
    """
    Create CMakeLists.txt file in wanted "cmake_path"

    :param context: the context of converter
    :type context: Context
    :param cmake_path: path where CMakeLists.txt should be open
    :type cmake_path: str
    :param open_type: type that CMakeLists.txt should be opened
    :type open_type: str
    :return: cmake file wrapper opened
    :rtype: _io.TextIOWrapper
    """

    if not cmake_path:
        if open_type == 'w':
            message(context, 'CMakeLists will be written at current directory.', 'warn')
        cmake = os.path.join(os.getcwd(), 'CMakeLists.txt')
    else:
        if open_type == 'w':
            message(context, 'CMakeLists.txt will be written at : ' + str(cmake_path), '')
        if cmake_path[-1:] == '/' or cmake_path[-1:] == '\\':
            cmake = str(cmake_path) + 'CMakeLists.txt'
        else:
            cmake = str(cmake_path) + '/CMakeLists.txt'

    if not os.path.exists(cmake) and open_type == 'r':
        return None

    return open(cmake, open_type, newline='\n', encoding='utf-8')
