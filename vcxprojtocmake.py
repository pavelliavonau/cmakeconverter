#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import etree
import ntpath as path
import sys, getopt, os

"""
Default Variable
"""
vcxproj = '../corealpi/platform/msvc/vc2015/elec.vcxproj'

def main(argv):

    ############ RECUPERATION OF VCXPROJ #############

    input_proj = ''
    try:
        opts, argv = getopt.getopt(argv, "hp", ["project="])
    except getopt.GetoptError:
        print('vcxprojtocmake.py -p <path/file.vcxproj>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('vcxprojtocmake.py -p <path/file.vcxproj>')
            sys.exit()
        elif opt in ("-p", "--project"):
            input_proj = arg

    if input_proj == '' or input_proj is None:
        input_proj = vcxproj

    tree = etree.parse(input_proj)
    ns = {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'}

    ############ GENERATION OF CMAKE #############

    cmakelist = open('CMakeLists.txt', 'w')
    try:


        """
        CMake Required
        """
        cmakelist.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

        """
        Project Name
        """
        projectname = tree.xpath('//ns:RootNamespace', namespaces=ns)[0]
        cmakelist.write('set(PROJECT_NAME ' + projectname.text + ')\n')

        # TODO Get a maximum of information to set flags after
        """
        Flags
        """
        warning = tree.xpath('//ns:WarningLevel', namespaces=ns)[0]
        lvl = '/W' + warning.text[-1:]
        print('Warning = ' + lvl)

        """
        Variables
        """
        # Cpp Dir
        cppfiles = tree.xpath('//ns:ClCompile', namespaces=ns)
        cpp_path = []
        c = 1
        for cpp in cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in cpp_path:
                    cpp_path.append(current_cpp)
                    cmakelist.write('set(CPP_DIR_' + str(c) + ' ' + current_cpp + '\n')
                    c += 1

        # Headers Dir
        headerfiles = tree.xpath('//ns:ClInclude', namespaces=ns)
        headers_path = []
        i = 1
        for header in headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in headers_path:
                headers_path.append(current_header)
                cmakelist.write('set(HEADER_DIR_' + str(i) + ' ' + current_header + '\n')
                i += 1

        # Project Name
        cmakelist.write('\n')
        cmakelist.write('project(${PROJECT_NAME} CXX)\n\n')

        """
        Definitions
        """
        preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
        cmakelist.write('add_definitions(\n')
        for preproc in preprocessor.text.split(";"):
            if preproc != '%(PreprocessorDefinitions)':
                cmakelist.write('   -D' + preproc + ' \n')
        cmakelist.write(')\n\n')

        """
        Dependencies
        """
        references = tree.xpath('//ns:ProjectReference', namespaces=ns)
        cmakelist.write('# Dépendances\nif(BUILD_DEPENDS)\n')
        for ref in references:
            reference = str(ref.get('Include'))
            cmakelist.write(
                '   add_subdirectory(${COREALPI_DIR}/platform/cmake/' + os.path.splitext(path.basename(reference))[0] + ')\n')
        cmakelist.write('else()\n')
        for ref in references:
            reference = str(ref.get('Include'))
            cmakelist.write('   link_directories(${COREALPI_DIR}/dependencies/' + os.path.splitext(path.basename(reference))[
                0] + '/build/${CMAKE_BUILD_TYPE})\n')
        cmakelist.write('endif()\n\n')

        """
        Files
        """
        cmakelist.write('file(GLOB SRC_FILES\n')
        x = 1
        while x < c:
            cmakelist.write('    ${CPP_DIR_' + str(x) + '}/*.cpp\n')
            x += 1
        j = 1
        while j < i:
            cmakelist.write('    ${HEADER_DIR_' + str(j) + '}/*.h\n')
            j += 1
        cmakelist.write(')\n\n')

        """
        Library and Executable
        """
        configurationtype = tree.find('//ns:ConfigurationType', namespaces=ns)
        if configurationtype.text == 'DynamicLibrary':
            cmakelist.write('add_library(${PROJECT_NAME} SHARED\n')
        elif configurationtype.text == 'StaticLibrary':
            cmakelist.write('add_library(${PROJECT_NAME} STATIC\n')
        else:
            cmakelist.write('add_executable(${PROJECT_NAME} \n')
        cmakelist.write('   ${SRC_FILES}\n')
        cmakelist.write(')\n\n')

        """
        Link and dependencies
        """
        cmakelist.write('target_link_libraries(${PROJECT_NAME} ')
        for ref in references:
            reference = str(ref.get('Include'))
            cmakelist.write(os.path.splitext(path.basename(reference))[0] + ' ')
        try:
            if tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0] is not None:
                depend = tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0]
                print('Additional Dependencies = ' + depend.text)
                listdepends = depend.text
                for d in listdepends.split(';'):
                    if d != '%(AdditionalDependencies)':
                        cmakelist.write(d + ' ')
        except IndexError:
            print('No dependencies')
        cmakelist.write(')')

    finally:
        cmakelist.close()

if __name__ == "__main__":
    main(sys.argv[1:])
