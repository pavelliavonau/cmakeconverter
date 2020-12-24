#!/usr/bin/env python3
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

import sys

try:
    from setuptools import setup, find_packages
except Exception:
    sys.exit("Error: missing python-setuptools library")

try:
    python_version = sys.version_info
except Exception:
    python_version = (1, 5)
if python_version < (3, 6):
    sys.exit(
        "This application requires a minimum of Python 3.6 !"
        " Please update your Python version."
    )

from cmake_converter import __description__, __version__, __license__, __author__, __project_url__
from cmake_converter import __name__ as __pkg_name__

# Requirements
install_requires = [
    'lxml',
    'colorama',
]


setup(
    name=__pkg_name__,
    version=__version__,

    license=__license__,

    # metadata for upload to PyPI
    author=__author__,
    author_email="liavonlida@gmail.com",
    keywords="cmake sln vcxproj vfproj visual cpp fortran CMakeLists",
    url=__project_url__,
    description=__description__,
    long_description=open('README.rst').read(),

    zip_safe=False,

    packages=find_packages(),
    python_requires='>=3.6',
    include_package_data=True,

    install_requires=install_requires,

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Libraries'
    ],

    entry_points={
        'console_scripts': [
            'cmake-converter = cmake_converter.main:main'
        ],
    }

)
