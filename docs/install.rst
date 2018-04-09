.. _install:

Install CMake Converter
***********************

Requirements
============

You must have **Python 3** installed to make this library work.

**Note:** CMake Converter is **not compatible** with Python 2 !

Installation (from Pip)
=======================

You can install CMake-Converter as a standard python library, with ``pip3``::

    # If you're under Windows, use "pip" instead "pip3"
    pip3 install cmake_converter

Installation (from Sources)
===========================

Clone and install
-----------------

To install from sources, you've to clone this repository and make a pip install::

    git clone https://github.com/algorys/cmakeconverter.git
    cd cmakeconverter
    # If you're under Windows, use "pip" instead "pip3"
    pip3 install .

External Libraries
------------------

You need to install Python modules that are listed in ``requirements.txt`` file with pip:

.. literalinclude:: ../requirements.txt