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

* **-p** : path to a valid **vcxproj** file. (``required``)
* **-c** : define output of CMakeLists.txt file
* **-a** : import cmake code from **file.cmake** (by convention, but any text file works) to the generated **CMakeLists.txt**.
* **-D** : replace dependencies found in **.vcxproj** by yours. This dependencies must be **separated by colons**.
* **-O** : define output of artefact produces by CMake. If this option is not specified, cmake-converter will try to get the one defined in **vcxproj**.
* **-i** : add include directories found in **vcxproj** in the generated **CMakeLists.txt**. Default : False

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

