#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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
    Converter Context for visual studio solution
    =========================
"""

from cmake_converter.context import Context

from .vcxproj.dependencies import VCXDependencies
from .vcxproj.flags import CPPFlags
from .vcxproj.project_files import VCXProjectFiles
from .vcxproj.project_variables import VCXProjectVariables
from .vcxproj.utils import VCXUtils
from .vcxproj.parser import VCXParser

from .vfproj.dependencies import VFDependencies
from .vfproj.flags import FortranFlags
from .vfproj.project_files import VFProjectFiles
from .vfproj.project_variables import VFProjectVariables
from .vfproj.utils import VFUtils
from .vfproj.parser import VFParser


class VSContext(Context):
    """
        Converter context for Visual Studio
    """
    def __init__(self):
        Context.__init__(self)

    def get_project_initialization_dict(self):
        return {
            '.vcxproj': self.init_context_for_vcxproj,
            '.vfproj': self.init_context_for_vfproj
        }

    def init_context_for_vcxproj(self):
        """Makes initialization of helpers for C/C++ projects."""
        self.variables = VCXProjectVariables()
        self.files = VCXProjectFiles()
        self.flags = CPPFlags()
        self.dependencies = VCXDependencies()
        self.utils = VCXUtils()
        self.parser = VCXParser()
        self.default_property_sheet = 'DEFAULT_CXX_PROPS'

    def init_context_for_vfproj(self):
        """Makes initialization of helpers for fortran projects."""
        self.variables = VFProjectVariables()
        self.files = VFProjectFiles()
        self.flags = FortranFlags()
        self.dependencies = VFDependencies()
        self.utils = VFUtils()
        self.parser = VFParser()
        self.default_property_sheet = 'DEFAULT_Fortran_PROPS'
