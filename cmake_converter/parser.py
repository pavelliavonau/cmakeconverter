#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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

"""
Module of Basic logic of parsers for Visual Solution projects
"""

import re

from cmake_converter.utils import message


class StopParseException(Exception):
    """ Just another well-named exception class for interrupting parsing """


class Parser:
    """
    Basic class of parsers for Visual Solution projects
    """
    def __init__(self):
        self.reset_setting_after_nodes = set()

    @staticmethod
    def parse(context):
        """ Basic implementation main parser entry point """
        message(context, 'Parser is not implemented yet!', 'error')

    @staticmethod
    def do_nothing_node_stub(context, node):
        """ Just stub for do nothing on handling node attempt """

    @staticmethod
    def do_nothing_attr_stub(context, attr_name, param, node):
        """ Just stub for do nothing on handling attribute attempt """

    def get_node_handlers_dict(self, context):
        """ Basic implementation of getting node handlers dict """
        raise NotImplementedError('You need to define a get_node_handlers_dict method!')

    def get_attribute_handlers_dict(self, context):
        """ Basic implementation of getting attribute handlers dict """
        raise NotImplementedError('You need to define a get_attribute_handlers_dict method!')

    def reset_current_setting_after_parsing_node(self, node):
        """ Remember node after parsing that current setting must be reset """
        self.reset_setting_after_nodes.add(node)

    @staticmethod
    def strip_namespace(tag):
        """ Removes namespace from xml tag """
        return re.sub(r'{.*\}', '', tag)

    def _parse_nodes(self, context, parent):
        for child_node in parent:
            if not isinstance(child_node.tag, str):
                continue
            child_node_tag = Parser.strip_namespace(child_node.tag)

            message(
                context,
                'Parsing... line {} node {} attrib {}'.format(
                    child_node.sourceline,
                    child_node_tag,
                    child_node.attrib
                ),
                ''
            )

            context.current_node = child_node

            try:
                self._parse_attributes(context, child_node)
            except StopParseException:
                context.current_node = parent
                continue

            node_handlers = self.get_node_handlers_dict(context)
            if child_node_tag in node_handlers:
                if child_node.text is not None:
                    child_node.text = child_node.text.strip()
                    node_handlers[child_node_tag](context, child_node)
            else:
                message(context, 'No handler for <{}> node.'.format(child_node_tag), 'warn3')

            if child_node in self.reset_setting_after_nodes:
                context.current_setting = (None, None)
                self.reset_setting_after_nodes.remove(child_node)

            context.current_node = parent

    def _parse_attributes(self, context, node):
        for attr in node.attrib:
            node_tag = Parser.strip_namespace(node.tag)
            node_key = '{}_{}'.format(node_tag, attr)
            attributes_handlers = self.get_attribute_handlers_dict(context)
            if node_key in attributes_handlers:    # node specified handler
                attributes_handlers[node_key](context, node_key, node.get(attr), node)
            elif attr in attributes_handlers:      # common attribute handler
                attributes_handlers[attr](context, attr, node.get(attr), node)
            else:
                message(
                    context,
                    'No handler for "{}" attribute of <{}> node.'.format(attr, node_tag),
                    'warn3'
                )
