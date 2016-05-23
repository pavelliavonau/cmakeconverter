# CMakeConverter

This project aims to facilitate the conversion of Visual Studio and QT to CMake projects.

## Goal

The goal of this project is to give to a Python script a `.vcxproj` or a `.pro` file and output a CMakeLists.txt. 

Actually, it only works with `vcxproj` and c/c++ project.

**This script still in development and has probably many issues**

## How to use

Make `vcxprojtocmake.py` executable :

`chmod +x vcxprojtocmake.py`

And run script like this :

`./vcxprojtocmake.py -p <path/to/file.vcxproj>`

You can also specify path in script itself in head of script.


