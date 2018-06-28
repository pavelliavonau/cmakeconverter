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

from cmake_converter.project_files import ProjectFiles


class VFProjectFiles(ProjectFiles):

    def get_source_files_descriptors(self, context):
        source_files_nodes = context.vcxproj['tree'].xpath('//File')
        file_node_attr = 'RelativePath'
        descriptors = [
            [
                context.sources,
                source_files_nodes,
                file_node_attr
            ]
        ]
        return descriptors

    def parse_file_node_options(self, context, file_node, node_text):
        for file_configuration_node in file_node:
            setting_name = file_configuration_node.get('Name')
            if setting_name not in context.settings:
                continue
            if node_text not in context.file_spec_raw_options:
                context.file_spec_raw_options[node_text] = {}
            context.file_spec_raw_options[node_text][setting_name] = {}
            for tool_node in file_configuration_node:
                tool_name = tool_node.get('Name')
                context.file_spec_raw_options[node_text][setting_name][tool_name] = tool_node.attrib
