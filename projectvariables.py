# -*- coding: utf-8 -*-

import message as msg

class ProjectVariables(object):
    """
    ProjectVariables : defines all the variables to be used by the project
    """
    out_deb_x86 = None
    out_deb_x64 = None
    out_rel_x86 = None
    out_rel_x64 = None

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.output = data['cmake_output']

    def define_variable(self):
        """
        Variable : define main variables in CMakeLists.
        :return header and cpp folder founds.
        """
        global out_deb_x86
        global out_deb_x64
        global out_rel_x86
        global out_rel_x64
        out_deb_x86 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        if out_deb_x86 is None:
            out_deb_x86 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]',
                namespaces=self.ns)
        out_deb_x64 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        if out_deb_x64 is None:
            out_deb_x64 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]',
                namespaces=self.ns)
        out_rel_x86 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        if out_rel_x86 is None:
            out_rel_x86 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]',
                namespaces=self.ns)
        out_rel_x64 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        if out_rel_x64 is None:
            out_rel_x64 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]',
                namespaces=self.ns)

        # CMake Minimum required.
        self.cmake.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

        # Project Name
        projectname = self.tree.xpath('//ns:RootNamespace', namespaces=self.ns)[0]
        self.cmake.write('################### Variables. ####################\n'
                         '# Change if you want modify path or other values. #\n'
                         '###################################################\n\n')
        self.cmake.write('set(PROJECT_NAME ' + projectname.text + ')\n')

        # Output DIR of artefacts
        self.cmake.write('# Output Variables\n')
        output_deb_x86 = ''
        output_deb_x64 = ''
        output_rel_x86 = ''
        output_rel_x64 = ''
        if self.output is None:
            if out_deb_x86 is not None:
                output_deb_x86 = out_deb_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if out_deb_x64 is not None:
                output_deb_x64 = out_deb_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if out_rel_x86 is not None:
                output_rel_x86 = out_rel_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if out_rel_x64 is not None:
                output_rel_x64 = out_rel_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
        else:
            output_deb_x86 = self.output
            output_deb_x64 = self.output
            output_rel_x86 = self.output
            output_rel_x64 = self.output

        if output_deb_x86 != '':
            msg.send('Output Debug x86 = ' + output_deb_x86, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG_X86 ' + output_deb_x86 + ')\n')
        if output_deb_x64 != '':
            msg.send('Output Debug x64 = ' + output_deb_x64, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG_X64 ' + output_deb_x64 + ')\n')
        if output_rel_x86 != '':
            msg.send('Output Release x86 = ' + output_rel_x86, 'ok')
            self.cmake.write('set(OUTPUT_REL_X86 ' + output_rel_x86 + ')\n')
        if output_deb_x64 != '':
            msg.send('Output Release x64 = ' + output_rel_x64, 'ok')
            self.cmake.write('set(OUTPUT_REL_X64 ' + output_rel_x64 + ')\n')

    def define_project(self):
        """
        Define Cmake Project
        """
        # Project Definition
        self.cmake.write('\n')
        self.cmake.write('############ Define Project. #############\n'
                         '# -- This the main options of project -- #\n'
                         '##########################################\n\n')
        self.cmake.write('project(${PROJECT_NAME} CXX)\n\n')

    def write_output(self):
        """
        Set output for each target
        """
        # TODO parse different target to see if debug or release
        # It'll use after variables define by :method define_variable