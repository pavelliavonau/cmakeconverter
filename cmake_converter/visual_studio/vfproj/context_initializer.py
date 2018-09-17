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

from cmake_converter.context_initializer import ContextInitializer
from cmake_converter.data_files import get_xml_data

from .dependencies import VFDependencies
from .flags import FortranFlags
from .project_files import VFProjectFiles
from .project_variables import VFProjectVariables
from .utils import VFUtils
from .parser import VFParser


class VFContextInitializer(ContextInitializer):
    def __init__(self, context, xml_project_path, cmake_lists_destination_path):
        ContextInitializer.__init__(self, context, xml_project_path, cmake_lists_destination_path)
        context.variables = VFProjectVariables()
        context.files = VFProjectFiles()
        context.flags = FortranFlags()
        context.dependencies = VFDependencies()
        context.utils = VFUtils()
        context.parser = VFParser()

    def init_context(self, context, vs_project):
        """
        Initialize context for given VS project

        :param context: converter context
        :type context: Context
        :param vs_project: VS project path (.vcxproj)
        :type vs_project: str
        """

        context.vcxproj = get_xml_data(context, vs_project)
