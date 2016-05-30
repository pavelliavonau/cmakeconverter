# CMakeConverter

This project aims to facilitate the conversion of Visual Studio (and QT in second time) to CMake projects.

## Introduction

The goal of this project is to give to a Python script a `.vcxproj` file and output a CMakeLists.txt.

Actually, it **only works** with `.vcxproj` and `c/c++` project.

# How to use

## Prerequisites

You may have **Python3** installed and **lxml** :

### Linux

`sudo apt-get install python3`

`pip install lxml`

### Windows

Go to [Python Releases for Windows](https://www.python.org/downloads/windows/) and download latest release. Install and follow instruction of setup.

Once Python installed, try to install `lxml` : `pip install lxml`

If installation of lxml fails, download binaries you need [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) and run :

`pip install <lxml-file.whl>`

That must be work. If no, try again in Administrator elevated terminal.

## Run script

**Note :** You can specify **file in head of script** if you want use this script always for the same project.

### Linux

Make `vcxprojtocmake.py` executable :

`chmod +x vcxprojtocmake.py`

And run script :

`./vcxprojtocmake.py -p <path/to/file.vcxproj>`

### Windows

Open a windows terminal (`WINDOWS-R` and type `cmd`). Go to the directory of script and run like this :

`python vcxprojtocmake.py -p <path/to/file.vcxproj>`

### Other options :

* -o : define output. Ex: "../../platform/cmake/"
* -I : add code from external file.

# Use CMake

**Cmakeconverter** try to have the most information as possible in your `file.vcxproj` ! However, it's recommended to read generated CMakeLists.txt before using.

## Variables

Actually, you have to place your generated CMakelists.txt in the **same** directory of your `.vcxproj` file, because he keep relative path of your project. Script make some incremental variable to keep the maximum of your source, but maybe you don't want to have all sources inside.

That's why you have the variable for your project like `PROJECT_NAME` or `DIR` in head of CMakeLists.txt. You can easily change this variable after.

## Definitions

After, you have MACRO and FLAGS definitions of project (like `UNICODE` for example). You can if needed add other MACRO like that : `-DMY_MACRO`.

## Build Dependencies

Dependencies are other projects you have set in your `.vcxproj` like shared or static libraries. You have an option call **BUILD_DEPENDS** who attempt to link with them.

If **ON** (default), he tries to find in another folder `platform/cmake/your_lib/` to build other `CMakeLists.txt`. This is a conventional directory structure and you can change it if needed.

If **OFF**, he tries to link library (`.so` or `.dll`) in a folder call `dependencies/libname/build`. This folder can also be change if needed.

## Flags

Flags are needed for compilation, mainly for Windows, to make compilation working. On Linux, flags are usually set properly.

## Files

`file` function add all your files to your project. Maybe you have to verify if all files are properly include !

## Add Library or Executable

After script get all information, he create your library (`STATIC` or `SHARED`) or your executable. If needed, he had dependencies too.

## Link

At end of file, you have directives to link your artefact with other project (external libraries).

## Cmake Compilation

Once you have verify CMakeLists.txt, copy it in your `.vcxproj` folder and run one of the following command :

```
cd ../to/root/project
mkdir build && cd build
# Generate Makefile
cmake ../path/to/cmakelist
# Build project
cmake --build .
```

If you have already compile dependencies :

```
cd ../to/root/project
mkdir build && cd build
# Generate Makefile
cmake -DBUILD_DEPENDS=OFF ../path/to/cmakelist
# Build project
cmake --build .
```

**Generators :** you can specify which Makefile you want generate, during makefile generation :

`-G"NMake Makefiles"`

Please [Cmake Generators](https://cmake.org/cmake/help/v3.5/manual/cmake-generators.7.html) for further details.

