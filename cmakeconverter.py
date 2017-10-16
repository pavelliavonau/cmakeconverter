#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, argparse
import message as msg
import convertdata as cv
import cmake, vcxproj

# class CMakeConverter(object):

def parse_argument():
    """
    Main script : define arguments and send to convertdata.
    """

    data = {
        'vcxproj': None,
        'cmake': None,
        'additional_code': None,
        'includes': None,
        'dependencies': None,
        'cmake_output': None,
        'data': None
    }

    # Init parser
    parser = argparse.ArgumentParser(description='Convert file.vcxproj to CMakelists.txt')
    parser.add_argument('-p', help='absolute or relative path of a file.vcxproj')
    parser.add_argument('-o', help='define output.')
    parser.add_argument('-a', help='import cmake code from file.cmake to your final CMakeLists.txt')
    parser.add_argument('-D', help='replace dependencies found in .vcxproj, separated by colons.')
    parser.add_argument('-O', help='define output of artefact produces by CMake.')
    parser.add_argument('-i', help='add include directories in CMakeLists.txt. Default : False')

    # Get args
    args = parser.parse_args()

    # Vcxproj Path
    if args.p is not None:
        temp_path = os.path.splitext(args.p)
        if temp_path[1] == '.vcxproj':
            msg.send('Project to convert = ' + args.p, '')
            project = vcxproj.Vcxproj()
            project.create_data(args.p)
            data['vcxproj'] = project.get_data()

    # CMakeLists.txt output
    if args.o is not None:
        cmakelists = cmake.CMake()
        if os.path.exists(args.o):
            cmakelists.create_cmake(args.o)
            data['cmake'] = cmakelists.cmake
        else:
            msg.send(
                'This path does not exist. CMakeList.txt will be generated in current directory.',
                'error'
            )
            cmakelists.create_cmake()
        data['cmake'] = cmakelists.cmake
    else:
        cmakelists = cmake.CMake()
        cmakelists.create_cmake()
        data['cmake'] = cmakelists.cmake

    # CMake additional Code
    if args.a is not None:
        data['additional_code'] = args.a

    # If replace Dependencies
    if args.D is not None:
        data['dependencies'] = args.D.split(':')

    # Define Output of CMake artefact
    if args.O is not None:
        data['cmake_output'] = args.O

    # Add include directories found in vcxproj
    if args.i is not None:
        if args.i == 'True':
            data['includes'] = True

    # Give all to class: conversata
    all_data = cv.ConvertData(data)
    all_data.create_data()


if __name__ == "__main__":
    parse_argument()
