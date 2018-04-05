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
    Message
    =======
     Manage sending messages during module execution
"""

import os


def send(message, status):  # pragma: no cover
    """
    Displays a message while the script is running

    :param message: content of the message
    :type message: str
    :param status: level of the message (change color)
    :type status: str
    """

    fail = ''
    warn = ''
    ok = ''
    endc = ''

    if os.name == 'posix':
        fail += '\033[91m'
        ok += '\033[34m'
        endc += '\033[0m'
        warn += '\033[93m'
    if status == 'error':
        print('ERR  : ' + fail + message + endc)
    elif status == 'warn':
        print('WARN : ' + warn + message + endc)
    elif status == 'ok':
        print('OK   : ' + ok + message + endc)
    else:
        print('INFO : ' + message)
