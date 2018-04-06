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
