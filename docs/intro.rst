.. _intro:

Introduction
************

About CMake Converter
=====================

CMake Converter is an open source software written in Python under the terms of the `GNU Affero General Public License <http://www.gnu.org/licenses/agpl.txt>`_ .

This application is for developers and integrators who want to automate the creation of ``CMakeLists.txt`` for their compilations, from Visual Studio's ``vcxproj`` files.

Features
========

CMake Converter converts your ``vcxproj`` file into ``CMakeLists.txt``.
He adds all the contained data such as compilation Flags, project targets, project dependencies, outputs of the produced binaries and more.

Release cycle
=============

CMake Converter has no strict schedule for releasing.

Other features will come in the next versions and you can propose new features through  `project issues <https://github.com/algorys/cmakeconverter/issues>`_.
Each feature is discussed in a separate issue.

About CMake
===========

In this documentation, you'll find some reminders about CMake and how the script handles your project's data inside.
For example, how the generated **CMakeLists.txt** manage dependencies.

But a minimum of knowledge on `CMake <https://cmake.org/documentation/>`_ is **recommended** !
