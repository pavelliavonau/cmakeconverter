# CMake Converter

[![Build Status](https://travis-ci.org/algorys/cmakeconverter.svg?branch=develop)](https://travis-ci.org/algorys/cmakeconverter)
[![Code Health](https://landscape.io/github/algorys/cmakeconverter/develop/landscape.svg?style=flat)](https://landscape.io/github/algorys/cmakeconverter/develop)
[![Coverage Status](https://coveralls.io/repos/github/algorys/cmakeconverter/badge.svg?branch=develop&service=github)](https://coveralls.io/github/algorys/cmakeconverter?branch=develop)
[![Documentation Status](http://readthedocs.org/projects/cmakeconverter/badge/?version=latest)](http://cmakeconverter.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/cmake_converter.svg)](https://badge.fury.io/py/cmake_converter)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## Introduction

This project aims to facilitate the conversion of Visual Studio projects to CMake projects. The goal is to give to a Python script, a **.vcxproj** file, and output a **CMakeLists.txt**.

**Note :** Actually, it's **only works** with `c/c++` projects.

## Quick Install & Run

### Install

You may have **Python3** installed to make this library works. Currently, **cmake-converter** is not available on **pip**.
So clone this repository and type the following command to install it:

```bash
# Inside repository folder
sudo pip install .
```

### Run

After install library, just run the script as below. Your `<file>.vcxproj` is of course required:

`cmake-converter -p <path/to/file.vcxproj>`

## Documentation

Documentation for CMake Converter is available on [Read The Docs](http://cmakeconverter.readthedocs.io).

## Bugs, issues and contributing

Contributions to this project are welcome and encouraged ... 
Issues in the project repository are the common way to raise an information.

