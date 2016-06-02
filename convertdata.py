# -*- coding: utf-8 -*-

import argparse, os
import message as msg

class ConvertData:
    """
    This class will convert data to CMakeLists.txt.
    """

    def __init__(self, arguments=None, cmake=None):
        self.arguments= arguments
        self.cmake = cmake

    def get_arguments(self):
        return self.arguments

    def get_cmake(self):
        return self.cmake
