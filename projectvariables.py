# -*- coding: utf-8 -*-

import message as msg

class ProjectVariables(object):

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
        # self.data = data
        # cmake = self.data['cmake']
        # tree = self.data['vcxproj']['tree']
        # ns = self.data['vcxproj']['ns']

        # CMake Minimum required.
        self.cmake.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

        # Project Name
        projectname = self.tree.xpath('//ns:RootNamespace', namespaces=self.ns)[0]
        self.cmake.write('# Variables. Change if you want modify path or other values.\n')
        self.cmake.write('set(PROJECT_NAME ' + projectname.text + ')\n')

        # Cpp Dir
        cppfiles = self.tree.xpath('//ns:ClCompile', namespaces=self.ns)
        cpp_path = []
        cpp_nb = 1
        for cpp in cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in cpp_path:
                    cpp_path.append(current_cpp)
                    self.cmake.write('set(CPP_DIR_' + str(cpp_nb) + ' ' + current_cpp + ')\n')
                    cpp_nb += 1
        # Headers Dir
        headerfiles = self.tree.xpath('//ns:ClInclude', namespaces=self.ns)
        headers_path = []
        header_nb = 1
        for header in headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in headers_path:
                headers_path.append(current_header)
                self.cmake.write('set(HEADER_DIR_' + str(header_nb) + ' ' + current_header + ')\n')
                header_nb += 1

        # Output DIR of artefacts
        self.cmake.write('# Output Variables\n')
        if self.output == '':
            path_debug_x86 = self.tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
                namespaces=self.ns)
            output_deb_x86 = path_debug_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_debug_x64 = self.tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
                namespaces=self.ns)
            output_deb_x64 = path_debug_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_release_x86 = self.tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
                namespaces=self.ns)
            output_rel_x86 = path_release_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_release_x64 = self.tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
                namespaces=self.ns)
            output_rel_x64 = path_release_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
        else:
            output_deb_x86 = self.output
            output_deb_x64 = self.output
            output_rel_x86 = self.output
            output_rel_x64 = self.output

        msg.send('Output Debug x86 = ' + output_deb_x86, 'ok')
        self.cmake.write('set(OUTPUT_DEBUG_X86 ' + output_deb_x86 + ')\n')

        msg.send('Output Debug x64 = ' + output_deb_x64, 'ok')
        self.cmake.write('set(OUTPUT_DEBUG_X64 ' + output_deb_x64 + ')\n')

        msg.send('Output Release x86 = ' + output_rel_x86, 'ok')
        self.cmake.write('set(OUTPUT_REL_X86 ' + output_rel_x86 + ')\n')

        msg.send('Output Release x64 = ' + output_rel_x64, 'ok')
        self.cmake.write('set(OUTPUT_REL_X64 ' + output_rel_x64 + ')\n')

        # Project Definition
        self.cmake.write('\n')
        self.cmake.write('# Define Project.\n')
        self.cmake.write('project(${PROJECT_NAME} CXX)\n\n')

    def set_output(self):
        """
        Set output for each target
        """
        self.cmake.write('# Define Output Debug of artefacts \n')
        out_x86d = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        out_x86r = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        out_x64d = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
            namespaces=self.ns)
        out_x64r = self.tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
            namespaces=self.ns)
        if out_x86d is not None and out_x86r is not None and out_x64d is not None and out_x64r is not None:
            self.cmake.write('option(x64 \n' +
                        '   "Define x64 output or x86 output" \n' +
                        '   ON \n' +
                        ')\n\n')
        if out_x86d is not None and out_x86r is not None:
            self.cmake.write('if(CMAKE_BUILD_TYPE STREQUAL "Debug")\n')
            self.cmake.write('  if(x64)\n')
            self.cmake.write('   set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X64}")\n')
            self.cmake.write('   set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X64}")\n')
            self.cmake.write('   set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X64}")\n')
            self.cmake.write('   message(STATUS "ARTEFACTS_OUTPUT = ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")\n')
            self.cmake.write('  else()\n')
            self.cmake.write('   set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X86}")\n')
            self.cmake.write('   set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X86}")\n')
            self.cmake.write('   set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_DEBUG_X86}")\n')
            self.cmake.write('   message(STATUS "ARTEFACTS_OUTPUT = ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")\n')
            self.cmake.write('  endif()\n')
            self.cmake.write('endif()\n')
        self.cmake.write('# Define Output Release of artefacts \n')
        if out_x64d is not None and out_x64r is not None:
            self.cmake.write('if(CMAKE_BUILD_TYPE STREQUAL "Release")\n')
            self.cmake.write('  if(x64)\n')
            self.cmake.write('   set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X64}")\n')
            self.cmake.write('   set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X64}")\n')
            self.cmake.write('   set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X64}")\n')
            self.cmake.write('   message(STATUS "ARTEFACTS_OUTPUT = ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")\n')
            self.cmake.write('  else()\n')
            self.cmake.write('   set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X86}")\n')
            self.cmake.write('   set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X86}")\n')
            self.cmake.write('   set(CMAKE_EXECUTABLE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${OUTPUT_RELEASE_X86}")\n')
            self.cmake.write('   message(STATUS "ARTEFACTS_OUTPUT = ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}")\n')
            self.cmake.write('  endif()\n')
            self.cmake.write('endif()\n')
        self.cmake.write('\n')