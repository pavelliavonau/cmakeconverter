# -*- coding: utf-8 -*-

class ConvertData:
    """
    This class will convert data to CMakeLists.txt.
    """

    def __init__(self, arguments=None):
        self.arguments= arguments

    def get_arguments(self):
        return self.arguments

    def get_cmake(self):
        return self.arguments['cmake']
