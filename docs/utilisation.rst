.. _utilisation:
.. code-block:: bash

Use CMake Converter
===================

Quick Use
---------

To use CMake Converter, simply give your ``vcxproj`` file to ``cmake-converter`` command::

    cmake-converter -p /path/to/your/vcxproj

Advanced Use
------------

The ``cmake-converter`` command accepts a lot of parameters to try to suit the majority of situations.

For example, you can add your own CMake code during the creation of the file or define to which folders your binaries will be placed during compilation.

You can always get help using the following command::

    cmake-converter -h

Here is the list of all possible parameters:

* ``'-p', '--project'``: **required** valid path to vcxproj file. i.e.: ../../mylib.vcxproj
* ``'-c', '--cmake'``: define output of CMakeLists.txt file.
* ``'-a', '--additional'``: import cmake code from file.cmake to your final CMakeLists.txt.
* ``'-D', '--dependencies'``: replace dependencies found in **.vcxproj**, separated by colons. i.e.: "external/zlib/cmake/:../../external/g3log/cmake/"
* ``'-O', '--cmakeoutput'``: define output of artefact produces by CMake.
* ``'-i', '--include'``: add include directories in CMakeLists.txt. Default : False.
* ``'-std', '--std'``: choose your C++ std version. Default : c++11.

Example
-------

Here is a full example where all parameters are used::

    cmake-converter \
    > -p ../project/platform/msvc/vc2015/mylib.vcxproj \
    > -a additional_code.cmake \
    > -o ../project/platform/cmake/mylib/ \
    > -D ../../../external/zlib/platform/cmake/:../../../external/g3log/platform/cmake/
    > -O ../../build/x64/\${CMAKE_BUILD_TYPE}/
    > -i
    > -std c++17

