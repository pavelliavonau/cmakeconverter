CMake Converter
===============

.. image:: https://travis-ci.org/algorys/cmakeconverter.svg?branch=develop
    :target: https://travis-ci.org/algorys/cmakeconverter
.. image:: https://landscape.io/github/algorys/cmakeconverter/develop/landscape.svg?style=flat
    :target: https://landscape.io/github/algorys/cmakeconverter/develop
    :alt: Code Health
.. image:: https://coveralls.io/repos/github/algorys/cmakeconverter/badge.svg?branch=develop
    :target: https://coveralls.io/github/algorys/cmakeconverter?branch=develop
.. image:: http://readthedocs.org/projects/cmakeconverter/badge/?version=develop
    :target: http://cmakeconverter.readthedocs.io/en/develop/?badge=develop
    :alt: Documentation Status
.. image:: https://badge.fury.io/py/cmake_converter.svg
    :target: https://badge.fury.io/py/cmake_converter
    :alt: Most recent PyPi version
.. image:: https://img.shields.io/badge/License-AGPL%20v3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0
    :alt: License AGPL v3

Introduction
------------

This project aims to facilitate the conversion of Visual Studio projects to CMake projects. The goal is to give to a Python script, a **.vcxproj** file, and output a **CMakeLists.txt**.

**Note :** Actually, it's **only works** with `c/c++` projects.

Quick Install & Run
-------------------

You may have **Python3** installed to make this library works !

Install from Pip
~~~~~~~~~~~~~~~~

Install cmake-converter as a standard python library::

    sudo pip install cmake_converter

Install from Source
~~~~~~~~~~~~~~~~~~~

Simply clone this repository and type the following command to install it::

    # Inside repository folder
    sudo pip install .

Run & Convert
~~~~~~~~~~~~~

After install library, just run the script as below. Your `<file>.vcxproj` is of course required::

    cmake-converter -p <path/to/file.vcxproj>`

Documentation
-------------

Documentation for CMake Converter is available on `Read The Docs <http://cmakeconverter.readthedocs.io/en/develop>`_.

Bugs, issues and contributing
-----------------------------

Contributions to this project are welcome and encouraged ... 
Issues in the project repository are the common way to raise an information.

For QMake
---------

If you're looking for QMake to CMake, please look at `qmake2cmake <https://github.com/digitalist/qmake2cmake>`_ by *digitalist*.
