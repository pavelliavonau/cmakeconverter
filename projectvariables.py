# -*- coding: utf-8 -*-

import message as msg

class ProjectVariables(object):

    def define_variable(self, data):
        """
        Variable : define main variables in CMakeLists.
        :return header and cpp folder founds.
        """
        cmake = data['cmake']
        tree = data['vcxproj']['tree']
        ns = data['vcxproj']['ns']
        # CMake Minimum required.
        cmake.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

        # Project Name
        projectname = tree.xpath('//ns:RootNamespace', namespaces=ns)[0]
        cmake.write('# Variables. Change if you want modify path or other values.\n')
        cmake.write('set(PROJECT_NAME ' + projectname.text + ')\n')

        # Cpp Dir
        cppfiles = tree.xpath('//ns:ClCompile', namespaces=ns)
        cpp_path = []
        cpp_nb = 1
        for cpp in cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in cpp_path:
                    cpp_path.append(current_cpp)
                    cmake.write('set(CPP_DIR_' + str(cpp_nb) + ' ' + current_cpp + ')\n')
                    cpp_nb += 1
        # Headers Dir
        headerfiles = tree.xpath('//ns:ClInclude', namespaces=ns)
        headers_path = []
        header_nb = 1
        for header in headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in headers_path:
                headers_path.append(current_header)
                cmake.write('set(HEADER_DIR_' + str(header_nb) + ' ' + current_header + ')\n')
                header_nb += 1

        # Output DIR of artefacts
        cmake.write('# Output Variables\n')
        if data['cmake_output'] == '':
            path_debug_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
                namespaces=ns)
            output_deb_x86 = path_debug_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_debug_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
                namespaces=ns)
            output_deb_x64 = path_debug_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_release_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
                namespaces=ns)
            output_rel_x86 = path_release_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
            path_release_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
                namespaces=ns)
            output_rel_x64 = path_release_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
        else:
            output_deb_x86 = data['cmake_output']
            output_deb_x64 = data['cmake_output']
            output_rel_x86 = data['cmake_output']
            output_rel_x64 = data['cmake_output']

        msg.send('Output Debug x86 = ' + output_deb_x86, 'ok')
        cmake.write('set(OUTPUT_DEBUG_X86 ' + output_deb_x86 + ')\n')

        msg.send('Output Debug x64 = ' + output_deb_x64, 'ok')
        cmake.write('set(OUTPUT_DEBUG_X64 ' + output_deb_x64 + ')\n')

        msg.send('Output Release x86 = ' + output_rel_x86, 'ok')
        cmake.write('set(OUTPUT_REL_X86 ' + output_rel_x86 + ')\n')

        msg.send('Output Release x64 = ' + output_rel_x64, 'ok')
        cmake.write('set(OUTPUT_REL_X64 ' + output_rel_x64 + ')\n')

        # Project Definition
        cmake.write('\n')
        cmake.write('# Define Project.\n')
        cmake.write('project(${PROJECT_NAME} CXX)\n\n')
        # return header_nb, cpp_nb