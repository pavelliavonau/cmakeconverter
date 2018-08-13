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

from cmake_converter.context import ContextInitializer
from cmake_converter.data_files import get_vcxproj_data, get_propertygroup, get_definitiongroup
from cmake_converter.utils import get_global_project_name_from_vcxproj_file, message

from .dependencies import VCXDependencies
from .flags import CPPFlags
from .project_files import VCXProjectFiles
from .project_variables import VCXProjectVariables
from .utils import VCXUtils
from .parser import VCXParser


class VCXContextInitializer(ContextInitializer):
    def __init__(self, context, xml_project_path, cmake_lists_destination_path):
        ContextInitializer.__init__(self, context, xml_project_path, cmake_lists_destination_path)
        context.variables = VCXProjectVariables()
        context.files = VCXProjectFiles()
        context.flags = CPPFlags()
        context.dependencies = VCXDependencies()
        context.utils = VCXUtils()
        context.parser = VCXParser()

    def init_context(self, context, vs_project):
        """
        Initialize context for given VS project

        :param context: converter context
        :type context: Context
        :param vs_project: VS project path (.vcxproj)
        :type vs_project: str
        """

        project_name = context.project_name
        context.vcxproj = get_vcxproj_data(context, vs_project)
        project_name_value = \
            get_global_project_name_from_vcxproj_file(context.vcxproj)
        if project_name_value:
            project_name = project_name_value
        context.project_name = project_name
