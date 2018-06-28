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

from cmake_converter.data_files import get_cmake_lists

from cmake_converter.utils import message
import cmake_converter.utils


class Context(object):
    """
        Converter context
    """
    def __init__(self):
        self.vcxproj = {}
        self.vcxproj_path = ''
        self.has_headers = False
        self.has_only_headers = False
        self.solution_languages = set()
        self.project_language = ''
        self.sln_deps = []
        self.target_references = []
        self.add_lib_deps = []
        self.add_lib_dirs = []
        self.packages = []

        self.additional_code = None
        self.dependencies = None
        self.cmake_output = None
        self.std = None
        self.dry = False
        self.is_converting_solution = False

        self.sln_configurations_map = None
        self.cmake = ''
        self.project_name = ''
        self.sources = {}
        self.headers = {}
        self.file_spec_raw_options = {}
        self.supported_architectures = set()
        self.settings = {}
        self.property_groups = {}
        self.definition_groups = {}
        self.property_sheets = []
        # helpera
        self.variables = None
        self.files = None
        self.flags = None
        self.dependencies = None


class ContextInitializer(object):
    def __init__(self, context, vs_project, cmake_lists_destination_path):
        self.init_files(context, vs_project, cmake_lists_destination_path)
        self.define_settings(context)

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
            message('Project to convert = ' + vs_project, '')
            context.project_name = project_name
            context.vcxproj_path = vs_project
            self.init_context(context, vs_project)
            self.set_cmake_lists_name(context, cmake_lists, context.project_name)

    @staticmethod
    def set_cmake_lists_name(context, cmake_lists, project_name):
        """
        Set CMakeLists.txt path in context, for given project

        :param context: converter context
        :type context: Context
        :param cmake_lists: path of CMakeLists related to project name
        :type cmake_lists: str
        :param project_name: name of project
        :type project_name: str
        """

        if cmake_lists:
            if os.path.exists(cmake_lists):
                cmake = get_cmake_lists(cmake_lists, 'r')
                cmake_converter.utils.path_prefix = ''
                if cmake:
                    file_text = cmake.read()
                    cmake.close()
                    if 'PROJECT_NAME {0}'.format(project_name) in file_text or file_text == '':
                        context.cmake = cmake_lists  # updating
                    else:
                        directory = cmake_lists + '/{0}_cmakelists'.format(project_name)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        context.cmake = directory
                        cmake_converter.utils.path_prefix = '../'
                        message('CMakeLists will be written at subdirectory.', 'warn')
                else:
                    context.cmake = cmake_lists  # writing first time

        if not context.cmake:
            message(
                'CMakeLists.txt path is not set. '
                'He will be generated in current directory.',
                'warn'
            )
            context.cmake = None



