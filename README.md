# CMakeConverter

## Introduction

This project aims to facilitate the conversion of Visual Studio projects to CMake projects. The goal is to give to a Python script, a **.vcxproj** file, and output a **CMakeLists.txt**.

**Note :** Actually, it's **only works** with `c/c++` projects.

# Prerequisites

You may have **Python3** installed and **lxml** module :

## On Linux

`sudo apt-get install python3`

`pip install lxml`

### On Windows

Go to [Python Releases for Windows](https://www.python.org/downloads/windows/) and download latest release. Install and follow instruction of setup.

Once Python installed, try to install `lxml` : `pip install lxml`

If installation of lxml fails, download binaries you need [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) and run :

`pip install <lxml-file.whl>`

That must be work. If no, try again in Administrator elevated terminal.

# Use the script

After install prerequisites, just run the script as below.

## Required

The `file.vcxproj` is of course required:

`./cmakeconverter.py -p <path/to/file.vcxproj>`

## Other options :

Script provides other option to facilitate conversion of your Visual Studio project :

* **-o** : define output of the geenrated `CMakeLists.txt`.
* **-a** : add cmake code from file (`file.cmake` is working too). Be sure your code is valid. Please read [CMake 3.5 Official Documentation](https://cmake.org/cmake/help/v3.5/release/3.5.html) to know more.
* **-D** : replace folder dependencies found in `.vcxproj` by other. Usefull for those who have other CMake project in other folders.
* **-O** : add possibility to define output of artefacts produces by CMake.
* **-i** : include additional directories if set "True". Default "False".

**Full Example :**

```bash
./cmakeconverter.py \
> -p ../project/platform/msvc/vc2015/mylib.vcxproj \
> -a additional_code.txt \
> -o ../project/platform/cmake/mylib/ \
> -D ../../../external/zlib/platform/cmake/:../../../external/g3log/platform/cmake/
> -O ../../build/x64/\${CMAKE_BUILD_TYPE}/
> -i True
```

# Use CMake

**Cmakeconverter** try to have the most information as possible in your `file.vcxproj` ! However, it's recommended to read and test generated CMakeLists.txt before using in production.

## Variables

Actually, you have to place your generated CMakelists.txt in the **same** directory of your `.vcxproj` file, because he keep relative path of your project. Script make some incremental variable to keep the maximum of your source, but maybe you don't want to have all sources inside.

That's why you have the variable for your project (like `PROJECT_NAME`) in head of CMakeLists.txt. You can easily change this variable after.

## Definitions

After these lines, you have MACRO and FLAGS definitions of project (like `UNICODE` for example). You can if needed add other MACRO like that : `-DYOUR_MACRO` or `-DYOUR_FLAGS`.

## Build Dependencies

Dependencies are other projects you have set in your `.vcxproj` like shared or static libraries. You have an option call **BUILD_DEPENDS** who attempt to link with them.

If **ON** (default), he tries to find in another folder `platform/cmake/your_lib/` to build other `CMakeLists.txt`. This is a conventional directory structure and you can override this with `-D` option of script.

If **OFF**, he tries to link library (`.so` or `.dll`) in a folder call `dependencies/libname/build`. This folder can also be change if needed.

## Flags

Flags are needed for compilation, mainly for Windows, to make compilation working. On Linux, flags are usually set properly but script add minimum to use.

## Files

`file` function add all your files to your project. In case of failing compilation, maybe you have to verify if all files are properly include !

## Add Library or Executable

After script get all information, he create your library (`STATIC` or `SHARED`) or your executable. If needed, he had dependencies too.

## Link

At end of file, you have directives to link your artefact with other project (external libraries).

## Cmake Compilation

Once you have verify CMakeLists.txt, copy it in your `.vcxproj` folder and run the following command :

```
cd ../to/root/project
mkdir build && cd build
# Generate Makefile
cmake ../path/to/cmakelist
# Build project
cmake --build .
```

You can add the following options to your cmake command :

```
# To link dependencies already compile
-DBUILD_DEPENDS=OFF
# To give target Debug. If not set Release will be default.
-DCMAKE_BUILD_TYPE=Debug
```

**Generators :** you can specify which Makefile you want generate, during makefile generation :

`-G"NMake Makefiles"`

Please refer to [Cmake Generators](https://cmake.org/cmake/help/v3.5/manual/cmake-generators.7.html) for further details.

