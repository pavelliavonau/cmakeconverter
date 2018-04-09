.. _use:

Use CMake Converter
*******************

Quick Use
=========

To use CMake Converter, simply give your ``vcxproj`` file to cmake-converter command::

    cmake-converter -p /path/to/your/project.vcxproj

Advance Usage
=============

The ``cmake-converter`` command accepts a lot of parameters to try to suit the majority of situations.

.. automodule:: cmake_converter.main

Project Conversion
==================

With the following project structure::

    project/
    ├── cmake
    │   ├── additional_code.txt
    │   └── File.cmake
    └── msvc
        ├── myexec.sln
        └── myexec.vcxproj

You can use cmake-converter as follows:

.. code-block:: bash

    cmake-converter \
    --project=../project/msvc/myexec.vcxproj \
    --cmake=../project/cmake/ \
    --cmakeoutput=../project/cmake \
    --additional=../project/cmake/additional_code.txt \
    --includecmake=../cmake/File.cmake \
    --std=c++17 \
    --include

Solution Conversion
===================

With CMake-Converter, you can also convert full Visual Studio solutions.
For the moment, this feature is still in BETA, but remains functional.

The script will extract data from all vcxproj and create the corresponding **CMakeLists.txt**.

**IMPORTANT:** Each ``vcxproj`` included in the solution must be in a **dedicated** directory, to ensure the smooth conversion.

**Note:** the ``--dependencies`` and ``--cmake`` parameters **can not** be used (and will not be used) during solution conversion !

With the following project structure::

    project/
    ├── externals
    │   └── cmake
    │       └── File.cmake
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
    --cmakeoutput=project/build/x64/ \
    --includecmake=../../externals/cmake/File.cmake \
    --std=c++17 \
    --include

And you'll have the following CMakeLists.txt generated::

    project/
    ├── externals
    │   └── cmake
    │       └── File.cmake
    └── msvc
        ├── libone
        │   ├── CMakeLists.txt *
        │   └── libone.vcxproj
        ├── libtwo
        │   ├── CMakeLists.txt *
        │   └── libtwo.vcxproj
        └── myexec
            ├── CMakeLists.txt *
            ├── myexec.sln
            └── myexec.vcxproj

Hints
=====

If you use **---cmake** parameter, ensure that given path has same directory level than your **.vcxproj**.

If you use **---includecmake** parameter, you have to give path relative to project itself, and not for script !

You can use CMake variables in parameters, by escaping ``$`` with a backslash. Example: ``--cmake=../\${CMAKE_BINARY_DIR}/x64``.

If you use variables defined by yourself, make sure that they are defined in a **.cmake** file or the code you are importing !


