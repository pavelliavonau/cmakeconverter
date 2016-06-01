# -*- coding: utf-8 -*-

import argparse, os
import message as msg

class InitData:
    """
    This class contain parameters of script and create cmake file.
    """
    def __init__(self):
        self.arguments= ''
        self.cmake = None

    def parse_argument(self):

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
        parser.add_argument('-I', help='import cmake filecode from text to your final CMakeLists.txt')
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

        """
        Constant Parameter
        ----------
        > Uncomment following line to use this script without parameters
        """
        vcxpath = 'example.vcxproj'

        # Collect args
        self.arguments = [
            vcxpath,
            output,
            additional_code,
            include,
            dependencies,
            cmake_output,
            data
        ]

        return self.arguments

    def create_cmake(self):
        if self.arguments[1] == '':
            msg.send('CMakeLists will be build in current directory.', 'ok')
        else:
            msg.send('CmakeLists.txt will be build in : ' + self.arguments[1], 'warn')
        cmakelists = str(self.arguments[1]) + 'CMakeLists.txt'

        self.cmake = open(cmakelists, 'w')

    def get_arguments(self):
        return self.arguments

    def get_cmake(self):
        return self.get_cmake()
