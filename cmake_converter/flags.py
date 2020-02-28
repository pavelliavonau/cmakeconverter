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
    Flags
    =====
     Manage compilation flags of project
"""

cl_flags = 'cl_flags'               # MSVC compile flags (Windows only)
ln_flags = 'ln_flags'               # MSVC link flags (Windows only)
ifort_cl_win = 'ifort_cl_win'       # ifort compile flags (Windows)
ifort_cl_unix = 'ifort_cl_unix'     # ifort compile flags (Unix)
ifort_ln_win = 'ifort_ln_win'       # ifort link flags for windows
ifort_ln_unix = 'ifort_ln_unix'     # ifort link flags for unix
defines = 'defines'                 # compile definitions (cross platform)
default_value = 'default_value'


# pylint: disable=R0903

class Flags:
    """
        Class who manage flags of projects
    """

    @staticmethod
    def get_no_default_lib_link_flags(flag_value):
        """Helper to get list of /NODEFAULTLIB flags"""
        ignore_libs = []
        if flag_value != '':
            for spec_lib in flag_value.split(';'):
                spec_lib = spec_lib.strip()
                if spec_lib:
                    ignore_libs.append('/NODEFAULTLIB:' + spec_lib)
        return ignore_libs

# pylint: enable=R0903
