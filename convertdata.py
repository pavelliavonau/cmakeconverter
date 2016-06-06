# -*- coding: utf-8 -*-

import projectvariables as pv
import message as msg
import projectfiles as pf
import macro, dependencies, flags

class ConvertData:
    """
    ConvertData: will convert data to CMakeLists.txt.
    """

    def __init__(self, data=None):
        self.data = data

    def create_data(self):
        # Write variables
        variables = pv.ProjectVariables(self.data)
        variables.define_variable()
        files = pf.ProjectFiles(self.data)
        files.write_variables()
        variables.define_project()
        variables.define_target()

        # Write Macro
        macros = macro.Macro()
        macros.write_macro(self.data)

        # Write Output Variables
        variables.write_output()

        # Write Include Directories
        depends = dependencies.Dependencies(self.data)
        if self.data['includes']:
            depends.write_include_dir()
        else:
            msg.send('Include Directories is not set.', '')

        # Write Dependencies
        depends.write_dependencies()

        # Add additional code or not
        if self.data['additional_code'] is not None:
            files.add_additional_code(self.data['additional_code'])

        # Write Flags
        all_flags = flags.Flags(self.data)
        all_flags.write_flags()

        # Write and add Files
        files.write_files()
        files.add_artefact()
