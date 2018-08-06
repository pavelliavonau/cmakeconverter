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

import os
import time
from multiprocessing import cpu_count

from cmake_converter.utils import message


class Context(object):
    """
        Converter context
    """
    def __init__(self):
        self.time0 = time.time()
        self.jobs = cpu_count()
        self.vcxproj = {}
        self.vcxproj_path = ''
        self.project_number = None
        self.has_headers = False
        self.has_only_headers = False
        self.solution_languages = set()
        self.project_languages = []
        self.sln_deps = []
        self.target_references = []
        self.add_lib_deps = False
        self.add_lib_dirs = []      # TODO: move to settings
        self.packages_config_path = ''
        self.import_projects = []
        self.packages = []

        self.additional_code = None
        self.dependencies = None
        self.cmake_output = None
        self.std = None
        self.dry = False
        self.silent = False
        self.warn_level = 3
        self.is_converting_solution = False

        self.sln_configurations_map = None
        self.solution_folder = ''
        self.configurations_to_parse = set()
        self.cmake = ''
        self.project_name = ''
        self.sources = {}
        self.headers = {}
        self.other_project_files = {}
        self.source_groups = {}
        self.file_spec_raw_options = {}
        self.supported_architectures = set()
        self.settings = {}
        self.current_setting = None
        self.property_groups = {}
        self.definition_groups = {}
        self.property_sheets = []
        # helpera
        self.parser = None
        self.variables = None
        self.files = None
        self.flags = None
        self.dependencies = None
        self.utils = None


class ContextInitializer(object):
    def __init__(self, context, vs_project, cmake_lists_destination_path):
        self.init_files(context, vs_project, cmake_lists_destination_path)
        message(
            context,
            'Initialization data for conversion of project {0}'.format(context.vcxproj_path),
            ''
        )
        self.define_settings(context)
        for sln_config in context.sln_configurations_map:
            context.configurations_to_parse.add(context.sln_configurations_map[sln_config])

    def define_settings(self, context):
        """
        Define settings of converter. Need to be defined.

        """

        raise NotImplementedError('You need to define a define_settings method!')

    def init_context(self, context, vs_project):
        """
        Initialize context

        """
        pass

    @staticmethod
    def init_context_setting(context, configuration_data):
        """
        Define settings of converter. Need to be reimplemented.

        :param context: converter context
        :type context: Context
        :param configuration_data: data of configuration (Debug|Win32, Release|x64,...)
        :type configuration_data: str
        """

        conf_arch = configuration_data.split('|')
        conf = conf_arch[0]
        arch = conf_arch[1]
        context.supported_architectures.add(arch)
        context.settings[configuration_data] = {
            'defines': [],
            'conf': conf,
            'arch': arch,
            'inc_dirs_list': [],
            'pre_build_events': [],
            'pre_link_events': [],
            'post_build_events': [],
        }

    def init_files(self, context, vs_project, cmake_lists):
        """
        Initialize opening of CMakeLists.txt and VS Project files

        :param context: converter context
        :type context: Context
        :param vs_project: Visual Studio project file path
        :type vs_project: str
        :param cmake_lists: CMakeLists.txt file path
        :type cmake_lists: str
        """

        if vs_project:
            temp_path = os.path.splitext(vs_project)
            project_name = os.path.basename(temp_path[0])
            context.project_name = project_name
            context.vcxproj_path = vs_project
            self.init_context(context, vs_project)
            self.set_cmake_lists_path(context, cmake_lists)

    @staticmethod
    def set_cmake_lists_path(context, cmake_lists):
        """
        Set CMakeLists.txt path in context, for given project

        :param context: converter context
        :type context: Context
        :param cmake_lists: path of CMakeLists related to project name
        :type cmake_lists: str
        """

        context_cmake = None

        if cmake_lists:
            if os.path.exists(cmake_lists):
                context_cmake = cmake_lists
        if context_cmake is None:
            message(
                context,
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
        if context:
            context.cmake = context_cmake

        return context_cmake


