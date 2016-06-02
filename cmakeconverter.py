#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, argparse
import message as msg
import convertdata as cv
import cmake

def parse_argument():
    """
    Main script : define arguments and send to convertdata.
    """

    vcxpath = ''
    output = ''
    additional_code = ''
    include = ''
    dependencies = ''
    cmake_output = ''
    data = ''

    # Init parser
    parser = argparse.ArgumentParser(description='Convert file.vcxproj to CMakelists.txt')
    parser.add_argument('-p', help='absolute or relative path of a file.vcxproj')
    parser.add_argument('-o', help='define output.')
    parser.add_argument('-I', help='import cmake.py filecode from text to your final CMakeLists.txt')
    parser.add_argument('-i', help='add include directories in CMakeLists.txt. Default : False')
    parser.add_argument('-D', help='replace dependencies found in .vcxproj by yours. Separated by colons.')
    parser.add_argument('-O', help='define output of artefact produces by CMake.')

    # Get args
    args = parser.parse_args()

    if args.p is not None:
        temp_path = os.path.splitext(args.p)
        if temp_path[1] == '.vcxproj':
            vcxpath = args.p
            msg.send('Project to convert = ' + args.p, '')
    if args.o is not None:
        if os.path.exists(args.o):
            output = args.o
            msg.send('Output = ' + args.o, 'ok')
        else:
            msg.send('This path does not exist. CMakeList will be generated in current directory.', 'error')
    if args.I is not None:
        additional_code = args.I

    if args.D is not None:
        dependencies = args.D.split(':')

    if args.O is not None:
        cmake_output = args.O

    if args.i is not None:
        if args.i == 'True':
            include = True

    # Collect args
    arguments = [
        vcxpath,
        additional_code,
        include,
        dependencies,
        cmake_output,
        data
    ]

    # Create CMake
    cmakelists = cmake.CMake()
    cmakelists.create_cmake(output)

    # Give all to class: conversata
    data = cv.ConvertData(arguments, cmakelists.get_cmake())
    for d in data.get_arguments():
        print('Data = ' + str(d))
    print('CMake = ' + str(data.get_cmake()))

if __name__ == "__main__":
    parse_argument()