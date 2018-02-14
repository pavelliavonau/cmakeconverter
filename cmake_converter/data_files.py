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
    Data Files
    ==========
     Manage the **VS Project** data and creation of **CMakeLists.txt** file
"""

from lxml import etree

from cmake_converter.message import send


def get_vcxproj_data(vs_project):
    """
    Return xml data from "vcxproj" file

    :param vs_project: the vcxproj file
    :type vs_project: str
    :return: dict with VS Project data
    :rtype: dict
    """

    vcxproj = {}

    try:
        tree = etree.parse(vs_project)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        vcxproj['tree'] = tree
        vcxproj['ns'] = ns
        assert 'http://schemas.microsoft.com' in ns['ns']
    except AssertionError:  # pragma: no cover
        send(
            '.vcxproj file cannot be import, because this file does not seem to comply with'
            ' Microsoft xml data !',
            'error'
        )
        exit(1)
    except (OSError, IOError):  # pragma: no cover
        send(
            '.vcxproj file cannot be import. '
            'Please, verify you have rights to this directory or file exists !',
            'error'
        )
        exit(1)
    except etree.XMLSyntaxError:  # pragma: no cover
        send('This file is not a ".vcxproj" file or XML is broken !', 'error')
        exit(1)

    return vcxproj


def get_propertygroup(target, platform, attributes=''):
    """
    Return "propertygroup" value for wanted platform and target

    :param target: wanted target: debug | release
    :type target: str
    :param platform: wanted platform: x86 | x64
    :type platform: str
    :param attributes: attributes to add to namespace
    :type attributes: str
    :return: "propertygroup" value
    :rtype: str
    """

    prop_deb_x86 = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"%s]' % \
        attributes
    prop_deb_x64 = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"%s]' % \
        attributes
    prop_rel_x86 = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"%s]' % \
        attributes
    prop_rel_x64 = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"%s]' % \
        attributes

    propertygroups = {
        'debug': {
            'x86': prop_deb_x86,
            'x64': prop_deb_x64,
        },
        'release': {
            'x86': prop_rel_x86,
            'x64': prop_rel_x64
        }
    }

    return propertygroups[target][platform]


def get_definitiongroup(target, platform):
    """
    Return ItemDefinitionGroup namespace depends on platform and target

    :param target: wanted target: debug | release
    :type target: str
    :param platform: wanted platform: x86 | x64
    :type platform: str
    :return: wanted ItemDefinitionGroup namespace
    :rtype: str
    """

    item_deb_x86 = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'Debug|Win32\'"]'
    item_deb_x64 = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'Debug|x64\'"]'
    item_rel_x86 = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'Release|Win32\'"]'
    item_rel_x64 = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'Release|x64\'"]'

    itemdefinitiongroups = {
        'debug': {
            'x86': item_deb_x86,
            'x64': item_deb_x64,
        },
        'release': {
            'x86': item_rel_x86,
            'x64': item_rel_x64
        }
    }

    return itemdefinitiongroups[target][platform]


def get_cmake_lists(cmake_path=None):
    """
    Create CMakeLists.txt file in wanted "cmake_path"

    :param cmake_path: path where CMakeLists.txt should be write
    :type cmake_path: str
    :return: cmake file wrapper opened
    :rtype: _io.TextIOWrapper
    """

    if not cmake_path:
        send('CMakeLists will be build in current directory.', '')
        cmake = open('CMakeLists.txt', 'w')
    else:
        send('CmakeLists.txt will be build in : ' + str(cmake_path), 'warn')
        if cmake_path[-1:] == '/' or cmake_path[-1:] == '\\':
            cmake = open(str(cmake_path) + 'CMakeLists.txt', 'w')
        else:
            cmake = open(str(cmake_path) + '/CMakeLists.txt', 'w')

    return cmake
