# -*- coding: utf-8 -*-

import projectvariables as pv
import macro

class ConvertData:
    """
    This class will convert data to CMakeLists.txt.
    """

    def __init__(self, data=None):
        self.data = data

    def create_data(self):
        # Write variables
        variables = pv.ProjectVariables(self.data)
        variables.define_variable()

        # Write Macro
        macro_project = macro.Macro()
        macro_project.set_macro_definition(self.data)

        # Write output variables
        variables.set_output()

    def get_arguments(self):
        return self.data

    def get_cmake(self):
        return self.data['cmake']
