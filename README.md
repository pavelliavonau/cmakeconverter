# CMakeConverter

This project aims to facilitate the conversion of Visual Studio and QT to CMake projects.

## Goal

The goal of this project is to give to a Python script a `.vcxproj` or a `.pro` file and output a CMakeLists.txt. 

Actually, it only works with `vcxproj` and `c/c++` project.

**This script still in development and has probably many issues**

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

That must be work. If no try in Administrator terminal.

### Run script

* On Linux

Make `vcxprojtocmake.py` executable :

`chmod +x vcxprojtocmake.py`

And run script like this :

`./vcxprojtocmake.py -p <path/to/file.vcxproj>`

* On Windows

Open a windows terminal (`WINDOWS-R` and type `cmd`). Go to the directory of script and run like this :

`python vcxprojtocmake.py -p <path/to/file.vcxproj>`

You can also specify **file in head of script** if you have any issue with **parameters** !


