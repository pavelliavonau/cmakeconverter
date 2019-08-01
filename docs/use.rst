.. _use:

Use CMake Converter
*******************

Quick Use
=========

To use cmake converter, simply give your ``*.sln`` file to cmake-converter command::

    cmake-converter -s <path/to/file.sln>

Advance Usage
=============

The ``cmake-converter`` command accepts a lot of parameters to try to suit the majority of situations.

.. automodule:: cmake_converter.main

Solution Conversion
===================

With cmake-converter, you can convert full Visual Studio solutions.

The script will extract data from all supported \*proj files and create the corresponding **CMakeLists.txt**.


With the following project structure::

    project/
    └── msvc
        ├── libone
        │   └── libone.vcxproj
        ├── libtwo
        │   └── libtwo.vcxproj
        └── myexec
            ├── myexec.sln
            └── myexec.vcxproj

Then you'll run cmake-converter as follow:

.. code-block:: bash

    cmake-converter \
    --solution=project/msvc/myexec/myexec.sln \
    --verbose-mode \
    --private-include-directories \
    --warning-level=3

And you'll have the following CMakeLists.txt generated::

    project/
    └── msvc
        ├── libone
        │   ├── CMakeLists.txt     *
        │   └── libone.vcxproj
        ├── libtwo
        │   ├── CMakeLists.txt     *
        │   └── libtwo.vcxproj
        └── myexec
            │  
            └── CMake              *
            │   ├── Default*.cmake *
            │   └── Utils.cmake    *
            ├── CMakeLists.txt     *
            ├── myexec.sln
            └── myexec.vcxproj

Hints
=====

You can add CMake/GlobalSettingsInclude.cmake file for global custom CMake settings.

Pay attention on warnings and do proposed fixes.

Run cmake-converter --help for more info.
