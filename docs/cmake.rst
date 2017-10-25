.. _cmake:

CMakeLists.txt Organization
===========================

**Important:** Actually, you have to place your generated CMakeLists.txt in the **same** directory of your `.vcxproj` file, because he keep relative path of your initial project.

Variables
---------

CMake Converter creates incremented generic variables at the top of the CMakeLists.txt to make it easier to modify.
Nothing prevents you from modifying them if something does not please you, but you will need to be careful with these changes.

Example:

If you change ``set(CPP_DIR_1 ../../../mylib/src)`` to ``set(CPP_DIR_1 ../../mylib/src)``, make sure that your *CMakeLists.txt* file has been moved accordingly, otherwise the path will be no longer good.

Project & Build Types
---------------------

After variables definitions, you'll have the project itself and the default build type used (**Release**). You can override this by::

    cmake . -DCMAKE_BUILD_TYPE=<TARGET>

**Note:** CMake Converter only manage *Debug* or *Release* build type, because Visual Studio projects doesn't manage other CMake build types like *RELWITHDEBINFO* or *MINSIZEREL*.

Definitions
-----------

After these lines, you have MACRO and FLAGS definitions of project (like `UNICODE` for example).
You can if needed add other MACRO like that : ``-DYOUR_MACRO`` or ``-DYOUR_FLAGS`` during CMake commands.

Artefacts Output
----------------

If you've or not use ``-O`` parameter with CMake Converter, he try to define default output for your binaries produced during compilation.
Each build type have a separate folder.

Build Dependencies
------------------

Dependencies are other projects you have set in your **vcxproj** project, like shared or static libraries.
You have an option call **BUILD_DEPENDS** who attempt to link with them.

By default this option is set to ``ON``.

If **ON**, CMake tries to find in another folder `platform/cmake/your_lib/` to build other `CMakeLists.txt`. This is a conventional directory structure and you can override this with `-D` option of script.

If **OFF**, he tries to link library (`.so` or `.dll`) in a folder call `dependencies/libname/build`. This folder can also be change if needed.

Flags
-----

The biggest part of the work done by CMake Converter, Flags are needed for compilation, mainly for Windows, to make compilation working.

On Linux, flags are usually set properly but script add minimum to use.

Files
-----

`file` function add all your files (contains inside variables) to your project. In case of failing compilation, maybe you have to verify if all files are properly include !

Add Library or Executable
-------------------------

After script get all information, he create your library (`STATIC` or `SHARED`) or your executable.

If needed, he add dependencies too and link them.

Use CMake
=========

CMake Converter try to have the most informations as possible of your **vcxproj** file.
However, it's recommended to read and test the generated **CMakeLists.txt** before using it in production !

Once CMake Converter has generated a **CMakeLists.txt** file, to compile with CMake, type the following commands::

    # It's better to create a dedicated folder:
    mkdir build && cd build
    # Generate the "Makefile"
    cmake ../to/cmakelists/folder/
    # Launch compilation
    cmake --build .

You can also provide a specific **Generator** with ``-G "<GENERATOR_NAME>"``. Please refer to `CMake Generator Documentation <https://cmake.org/cmake/help/v3.5/manual/cmake-generators.7.html>`_.

You can provide the build type by add ``-DCMAKE_BUILD_TYPE=<BUILD_TYPE>``.

CMake provides a lot of other options that you can discover in their official documentation.

