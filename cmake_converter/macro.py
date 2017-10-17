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
    Macro manage creation of project Macros ("-D" instructions)
"""


class Macro(object):
    """
        Class who check and write project macros
    """

    @staticmethod
    def write_macro(data):
        """
        Get Macro definitions and write to cmake file.

        """

        tree = data['vcxproj']['tree']
        ns = data['vcxproj']['ns']
        cmake = data['cmake']

        preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
        if preprocessor.text:
            cmake.write('# Definition of Macros\n')
            cmake.write('add_definitions(\n')
            for preproc in preprocessor.text.split(";"):
                if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                    cmake.write('   -D%s \n' % preproc)
            # Unicode
            u = tree.find("//ns:CharacterSet", namespaces=ns)
            if 'Unicode' in u.text:
                cmake.write('   -DUNICODE\n')
                cmake.write('   -D_UNICODE\n')
            cmake.write(')\n\n')
