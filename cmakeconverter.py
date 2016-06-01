# -*- coding: utf-8 -*-

import sys, argparse, os
import message as msg
import vcxproj as vs

class CMakeConverter(object):
    """
    This class get parameters.
    """
    def __init__(self):
        self.path = ''
        self.output = ''
        self.additional_code = ''
        self.include = ''
        self.dependencies = ''
        self.cmake_output = ''
        self.data = None

    def parse_argument(self):
        try:
            parser = argparse.ArgumentParser(description='Convert file.vcxproj to CMakelists.txt')
            parser.add_argument('-p', help='absolute or relative path of a file.vcxproj')
            parser.add_argument('-o', help='define output.')
            parser.add_argument('-I', help='import cmake filecode from text to your final CMakeLists.txt')
            parser.add_argument('-i', help='add include directories in CMakeLists.txt. Default : False')
            parser.add_argument('-D', help='replace dependencies found in .vcxproj by yours. Separated by colons.')
            parser.add_argument('-O', help='define output of artefact produces by CMake.')
            args = parser.parse_args()
            if args.p is not None:
                temp_path = os.path.splitext(args.p)
                if temp_path[1] == '.vcxproj':
                    self.path = args.p
                    msg.send('Project to convert = ' + args.p, '')
            if args.o is not None:
                if os.path.exists(args.o):
                    self.output = args.o
                    msg.send('Output = ' + args.o, 'ok')
                else:
                    msg.send('This path does not exist. CMakeList will be generated in current directory.', 'error')
            if args.I is not None:
                self.additional_code = args.I

            if args.D is not None:
                self.dependencies = args.D.split(':')

            if args.O is not None:
                self.cmake_output = args.O

            if args.i is not None:
                if args.i == 'True':
                    self.include = True

            """
            Constant Parameter
            ----------
            > Uncomment following line to use this script without parameters
            """
            self.path = '../corealpi/platform/msvc/vc2015/elec.vcxproj'

            temp_data = vs.Vcxproj()
            temp_data.create_data(self.path)
            self.data = temp_data.get_data()


            print('test = ' + str(self.data))

        except argparse.ArgumentError:
            sys.exit()