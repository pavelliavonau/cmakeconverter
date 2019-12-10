CMake Converter
===============

.. image:: https://travis-ci.org/pavelliavonau/cmakeconverter.svg?branch=develop
    :target: https://travis-ci.org/pavelliavonau/cmakeconverter
.. image:: https://landscape.io/github/pavelliavonau/cmakeconverter/develop/landscape.svg?style=flat
    :target: https://landscape.io/github/pavelliavonau/cmakeconverter/develop
    :alt: Code Health
.. image:: https://coveralls.io/repos/github/pavelliavonau/cmakeconverter/badge.svg?branch=develop
    :target: https://coveralls.io/github/pavelliavonau/cmakeconverter?branch=develop
.. image:: http://readthedocs.org/projects/cmakeconverter/badge/?version=develop
    :target: http://cmakeconverter.readthedocs.io/en/develop/?badge=develop
    :alt: Documentation Status
.. image:: https://badge.fury.io/py/cmake-converter.svg
    :target: https://badge.fury.io/py/cmake-converter
    :alt: Most recent PyPi version
.. image:: https://img.shields.io/pypi/pyversions/cmake_converter.svg
    :target: https://pypi.org/project/cmake_converter/
    :alt: Supported Python versions
.. image:: https://img.shields.io/badge/License-AGPL%20v3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0
    :alt: License AGPL v3
.. image:: https://img.shields.io/badge/Donate-PayPal-green.svg
    :target: https://www.paypal.me/pavelliavonau

Introduction
------------

This project aims to facilitate the conversion of Visual Studio solution to CMake projects.
The goal is to give to a Python script, a **\*.sln** file, and output a set of **CMakeLists.txt** that may be used for generating visual studio solution backward as perfect as possible. Project is useful for porting VS projects into CMake build system.

**Note :** Actually, it's **only works** with  ``C/C++`` (\*.vcxproj) and ``Fortran`` (\*.vfproj) projects.

Install & Run
-------------

Install package from PyPI
~~~~~~~~~~~~~~~~~~~~~~~~~

Install last stable release of cmake-converter::

    pip install cmake-converter

**Note :** **If you found an issue** in the package installed from pip, please, **do not create github issue at once** and check for pre-release version (pip -pre) or last source from develop first. It might be has fixed already and ready to release.

Install package from source code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Simply clone or download  the repository and type the following command to install it::

    # Inside repository folder.
    pip install .

Run
~~~

After install library, just run the script as below. Your ``*.sln`` file is of course required::

    cmake-converter -s <path/to/file.sln>

**Note :** If you satisfied with conversion, give a star to the project and consider to donate, please.

Documentation
-------------

Documentation for CMake Converter is available on `Read The Docs <http://cmakeconverter.readthedocs.io/en/develop>`_.

Bugs, issues and contributing
-----------------------------

Contributions to this project are welcome and encouraged ... 
Issues in the project repository are the common way to raise an information.

**Note:** if you have an issue, please provide me if possible the visual studio project involved.

Donations
--------------------------

If you appreciate my efforts related to this project, give me a gift. I'll be glad to get some money working for free ;)
To make a donation - please press the button below.

.. image:: https://raw.githubusercontent.com/stefan-niedermann/paypal-donate-button/master/paypal-donate-button.png
    :target: https://www.paypal.me/pavelliavonau