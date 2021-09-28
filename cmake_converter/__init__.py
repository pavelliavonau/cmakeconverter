#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020:
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

"""
    CMakeConverter

    This module is a command line program who allow you to convert .vcxproj file
    to CMakeLists.txt file.
"""

# Application version and manifest
VERSION = (2, 2, 0)
__application__ = "CMake-Converter"
__short_version__ = '.'.join((str(each) for each in VERSION[:2]))
__version__ = '.'.join((str(each) for each in VERSION[:4]))
__author__ = "Liavonau Pavel"
__copyright__ = "2016-2020 - %s" % __author__
__license__ = "GNU Affero General Public License, version 3"
__description__ = "CMake converter for Visual Studio projects"
__releasenotes__ = "CMake converter for Visual Studio projects"
__project_url__ = "https://github.com/pavelliavonau/cmakeconverter"
__doc_url__ = "https://github.com/pavelliavonau/cmakeconverter"

# Application Manifest
manifest = {
    'name': __application__,
    'version': __version__,
    'author': __author__,
    'description': __description__,
    'copyright': __copyright__,
    'license': __license__,
    'release': __releasenotes__,
    'url': __project_url__,
    'doc': __doc_url__
}
