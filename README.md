# CMakeConverter

This project aims to facilitate the conversion of Visual Studio (and QT in second time) to CMake projects.

## Goal

The goal of this project is to give to a Python script a `.vcxproj` file and output a CMakeLists.txt.

Actually, it **only works** with `vcxproj` and `c/c++` project.

> **This script still in development and has probably many issues**

## How to use

### Prerequisites

You may have **Python3** installed and **lxml** :

* On Linux

`sudo apt-get install python3`

`pip install lxml`

* On Windows

Go to [Python Releases for Windows](https://www.python.org/downloads/windows/) and download latest release. Install and follow instruction of setup.

Once Python installed, try to install `lxml` : `pip install lxml`

If installation of lxml fails, download binaries you need [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml) and run :

`pip install <lxml-file.whl>`

That must be work. If no, try again in Administrator elevated terminal.

### Run script

* On Linux

Make `vcxprojtocmake.py` executable :

`chmod +x vcxprojtocmake.py`

And run script like this :

`./vcxprojtocmake.py -p <path/to/file.vcxproj>`

* On Windows

Open a windows terminal (`WINDOWS-R` and type `cmd`). Go to the directory of script and run like this :

`python vcxprojtocmake.py -p <path/to/file.vcxproj>`

> You can also specify **file in head of script** if you have any issue with **parameters** ! (Normally fix in last version)

# Use CMake after

**Cmakeconverter** try to have the most information as possible in your `file.vcxproj` ! 

## Variables

Normally, you have to place your generated CMakelists.txt in the **same** directory of your `.vcxproj` file, because he keep relative path of your project. Script make some incremental variable to keep the maximum of your source, but maybe you don't want to have all sources inside.

That's why you have the variable for your project like `PROJECT_NAME` or `DIR` in head of CMakeLists.txt. You can easily change this variable after.

## Definitions

After, you have MACRO definitions of project (like `UNICODE` for example). You can if needed add other MACRO like that : `-DMY_MACRO`.

## Build Dependencies

Dependencies are other project you have set in your `.vcxproj` like shared library. You have an option call **BUILD_DEPENDS** who try to find in different folder.

If **ON** (default), he tries to find in folder `platform/cmake/your_lib/` an another `CMakeLists.txt`. This is a conventional directory structure and you can change it if needed.

If **OFF**, he tries to link library (`.so` or `.dll`) in a folder call `dependencies/libname/build`. This folder can be change also if needed.

## Flags

Flags are needed for compilation, mainly for Windows, to make compilation working. On Linux, flags are usually set properly.

## Files

`file` function add all your files with wildcard for your project. Maybe you have to verify if all files are properly include !

## Add Library or Executable

After script get all information, he create your library (`STATIC` or `SHARED`) or your executable. If needed, he had dependencies too.

## Link

In end of file, you have the directive to link your artefact with other project (other libraries or external).

## Cmake Command

Once you have verify CMakeLists.txt, copy it in your .vcxpro folder and run one of the following command :

```
cd ../to/root/project
mkdir build && cd build
cmake ../path/to/cmakelist
cmake --build .
```

If you have already compile dependencies :

```
cd ../to/root/project
mkdir build && cd build
cmake -DBUILD_DEPENDS=OFF ../path/to/cmakelist
cmake --build .
```

# Bugs

Please report any issue in this repos. That's my first script in Python so there is probably some issues for situation I've no planned.

Please Star repos if you like it :)
