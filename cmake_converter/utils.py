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
    Utils
    =====
    Utils manage function needed by converter
"""

import colorama

DONE = colorama.Fore.GREEN + colorama.Style.BRIGHT
OK = colorama.Fore.CYAN + colorama.Style.BRIGHT
WARN = colorama.Fore.YELLOW + colorama.Style.BRIGHT
FAIL = colorama.Fore.RED + colorama.Style.BRIGHT
ENDC = colorama.Fore.RESET + colorama.Style.RESET_ALL


def message(text, status):  # pragma: no cover
    """
    Displays a message while the script is running

    :param text: content of the message
    :type text: str
    :param status: level of the message (change color)
    :type status: str
    """

    if status == 'error':
        print('ERR  : ' + FAIL + text + ENDC)
    elif status == 'warn':
        print('WARN : ' + WARN + text + ENDC)
    elif status == 'ok':
        print('OK   : ' + OK + text + ENDC)
    elif status == 'done':
        print(DONE + text + ENDC)
    else:
        print('INFO : ' + text)


def get_title(title, text):
    """
    Return formatted title for writing

    :param title: main title text
    :type title: str
    :param text: text related to title
    :type text: str
    :return: formatted title
    :rtype: str
    """

    offset = 60
    text_offset = (offset / 2) - len(title)

    title_sharp = ''
    for _ in range(int(text_offset)):
        title_sharp = '%s#' % title_sharp

    title = '%s %s ' % (title_sharp, title)
    i = len(title)
    while i < offset:
        title = '%s#' % title
        i += 1

    text = '# %s' % text

    i = len(text)
    while i < offset:
        if i < offset - 1:
            text = '%s ' % text
        else:
            text = '%s#' % text
            break
        i += 1

    bottom_text = ''
    for _ in range(offset):
        bottom_text = '%s#' % bottom_text

    return '%s\n%s\n%s\n\n' % (title, text, bottom_text)
