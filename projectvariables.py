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
    out_deb = False
    out_rel = False

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.output = data['cmake_output']

    def define_variable(self):
        """
        Variable : define main variables in CMakeLists.
        """
        ProjectVariables.out_deb_x86 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        if ProjectVariables.out_deb_x86 is None:
            ProjectVariables.out_deb_x86 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]',
                namespaces=self.ns)
        ProjectVariables.out_deb_x64 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        if ProjectVariables.out_deb_x64 is None:
            ProjectVariables.out_deb_x64 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]',
                namespaces=self.ns)
        ProjectVariables.out_rel_x86 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        if ProjectVariables.out_rel_x86 is None:
            ProjectVariables.out_rel_x86 = self.tree.find(
                '//ns:PropertyGroup/ns:OutDir[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]',
                namespaces=self.ns)
        ProjectVariables.out_rel_x64 = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        if ProjectVariables.out_rel_x64 is None:
            ProjectVariables.out_rel_x64 = self.tree.find(
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
            if ProjectVariables.out_deb_x86 is not None:
                output_deb_x86 = ProjectVariables.out_deb_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_deb_x64 is not None:
                output_deb_x64 = ProjectVariables.out_deb_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_rel_x86 is not None:
                output_rel_x86 = ProjectVariables.out_rel_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            if ProjectVariables.out_rel_x64 is not None:
                output_rel_x64 = ProjectVariables.out_rel_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
        elif self.output:
            if self.output[-1:] == '/' or self.output[-1:] == '\\':
                build_type = '${CMAKE_BUILD_TYPE}'
            else:
                build_type = '/${CMAKE_BUILD_TYPE}'
            output_deb_x86 = self.output + build_type
            output_deb_x64 = self.output + build_type
            output_rel_x86 = self.output + build_type
            output_rel_x64 = self.output + build_type
        else:
            output_deb_x86 = ''
            output_deb_x64 = ''
            output_rel_x86 = ''
            output_rel_x64 = ''

        if output_deb_x64 != '':
            msg.send('Output Debug = ' + output_deb_x64, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG ' + output_deb_x64 + ')\n')
            ProjectVariables.out_deb = True
        elif output_deb_x86 != '':
            msg.send('Output Debug = ' + output_deb_x86, 'ok')
            self.cmake.write('set(OUTPUT_DEBUG ' + output_deb_x86 + ')\n')
            ProjectVariables.out_deb = True
        else:
            msg.send('No Output Debug define.', '')

        if output_rel_x64 != '':
            msg.send('Output Release = ' + output_rel_x64, 'ok')
            self.cmake.write('set(OUTPUT_REL ' + output_rel_x64 + ')\n')
            ProjectVariables.out_rel = True
        elif output_rel_x86 != '':
            msg.send('Output Release = ' + output_rel_x86, 'ok')
            self.cmake.write('set(OUTPUT_REL ' + output_rel_x86 + ')\n')
            ProjectVariables.out_rel = True
        else:
            msg.send('No Output Release define.', '')

    def define_project(self):
        """
        Define Cmake Project
        """
        # Project Definition
        self.cmake.write('\n')
        self.cmake.write('############## Define Project. ###############\n'
                         '# ---- This the main options of project ---- #\n'
                         '##############################################\n\n')
        self.cmake.write('project(${PROJECT_NAME} CXX)\n\n')

    def define_target(self):
        """
        Define target release if not define.
        """
        self.cmake.write('# Define Release by default.\n'
                         'if(NOT CMAKE_BUILD_TYPE)\n'
                         '  set(CMAKE_BUILD_TYPE "Release")\n'
                         '  message(STATUS "Build type not specified: defaulting to release.")\n'
                         'endif(NOT CMAKE_BUILD_TYPE)\n\n')

    def write_output(self):
        """
        Set output for each target
        """
        if ProjectVariables.out_deb or ProjectVariables.out_rel:
            self.cmake.write('############## Artefacts Output #################\n')
            self.cmake.write('# Defines outputs , depending Debug or Release. #\n')
            self.cmake.write('#################################################\n\n')
            if ProjectVariables.out_deb:
                self.cmake.write('if(CMAKE_BUILD_TYPE STREQUAL "Debug")\n')
                self.cmake.write('  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")\n')
                self.cmake.write('  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")\n')
                self.cmake.write('  set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG}")\n')
            if ProjectVariables.out_rel:
                self.cmake.write('else()\n')
                self.cmake.write('  set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n')
                self.cmake.write('  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n')
                self.cmake.write('  set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_REL}")\n')
                self.cmake.write('endif()\n\n')
        else:
            msg.send('No Output found or define. CMake will use default ouputs.', 'warn')
