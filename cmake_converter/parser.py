#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Pavel Liavonau, liavonlida@gmail.com
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

from cmake_converter.utils import message


class Parser(object):

    @staticmethod
    def parse(context):
        message(context, 'Parser is not implemented yet!', 'error')

    @staticmethod
    def do_nothing_stub(context, param, node):
        pass

    @staticmethod
    def remove_unused_settings(context):
        mapped_configurations = set()
        for sln_config in context.sln_configurations_map:
            mapped_configurations.add(context.sln_configurations_map[sln_config])
        settings_to_remove = []
        for setting in context.settings:
            if setting not in mapped_configurations:
                settings_to_remove.append(setting)
        for setting in settings_to_remove:
            context.settings.pop(setting, None)
