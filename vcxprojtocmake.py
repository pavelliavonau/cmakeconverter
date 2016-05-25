#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import etree
import ntpath as path
import sys, getopt, os, re

"""
Default Variable
"""
FAIL = '\033[91m'
OKBLUE = '\033[34m'
ENDC = '\033[0m'

def main(argv):

    ############ RECUPERATION OF VCXPROJ #############

    input_proj = ''
    try:
        opts, argv = getopt.getopt(argv, "hp", ["project="])
    except getopt.GetoptError:
        print('vcxprojtocmake.py -p <path/file.vcxproj>')
        sys.exit()
    for opt, arg in opts:
        if opt == '-h':
            print('vcxprojtocmake.py -p <path/file.vcxproj>')
            sys.exit()
        elif opt in ("-p", "--project"):
            input_proj = arg

    """
    STATIC FILE : Uncomment following lines to use this script without parameters
    """
    #vcxproj = '../corealpi/platform/msvc/vc2015/elec.vcxproj'
    #input_proj = vcxproj

    try:
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
                    # Unicode
            u = tree.find("//ns:CharacterSet", namespaces=ns)
            if 'Unicode' in u.text:
                cmakelist.write('   -DUNICODE\n')
                cmakelist.write('   -D_UNICODE\n')
            cmakelist.write(')\n\n')

            """
            Dependencies
            """
            references = tree.xpath('//ns:ProjectReference', namespaces=ns)
            cmakelist.write('# Dependencies\nif(BUILD_DEPENDS)\n')
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
            Flags
            """
            release_flags = ''
            debug_flags = ''

            # Warning
            warning = tree.xpath('//ns:WarningLevel', namespaces=ns)[0]
            lvl = ' /W' + warning.text[-1:]
            debug_flags += lvl
            release_flags += lvl

            # WholeProgramOptimization
            gl_debug_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:WholeProgramOptimization',
                namespaces=ns)
            gl_debug_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:WholeProgramOptimization',
                namespaces=ns)
            if gl_debug_x86 is not None and gl_debug_x64 is not None:
                if 'true' in gl_debug_x86.text and 'true' in gl_debug_x64.text:
                    debug_flags += ' /GL'
            gl_release_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:WholeProgramOptimization',
                namespaces=ns)
            gl_release_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:WholeProgramOptimization',
                namespaces=ns)
            if gl_release_x86 is not None and gl_release_x64 is not None:
                if 'true' in gl_release_x86.text and 'true' in gl_release_x64.text:
                    release_flags += ' /GL'

            # UseDebugLibraries
            md_debug_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:UseDebugLibraries',
                namespaces=ns)
            md_debug_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:UseDebugLibraries',
                namespaces=ns)
            if md_debug_x64 is not None and md_debug_x86 is not None:
                if 'true' in md_debug_x86.text and 'true' in md_debug_x64.text:
                    debug_flags += ' /MDd'
            md_release_x86 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:UseDebugLibraries',
                namespaces=ns)
            md_release_x64 = tree.find(
                '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:UseDebugLibraries',
                namespaces=ns)
            if md_release_x86 is not None and md_release_x64 is not None:
                if 'true' in md_release_x86.text and 'true' in md_release_x64.text:
                    release_flags += ' /MDd'

            # Optimization
            opt_debug_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:Optimization',
                namespaces=ns)
            opt_debug_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:Optimization',
                namespaces=ns)
            if opt_debug_x86 is not None and opt_debug_x64 is not None:
                if 'Disabled' in opt_debug_x64.text and 'Disabled' in opt_debug_x86.text:
                    debug_flags += ' /O2'
            opt_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:Optimization',
                namespaces=ns)
            opt_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:Optimization',
                namespaces=ns)
            if opt_release_x86 is not None and opt_release_x64 is not None:
                if 'MaxSpeed' in opt_release_x64.text and 'MaxSpeed' in opt_release_x86.text:
                    release_flags += ' /O2'

            # IntrinsicFunctions
            oi_debug_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:IntrinsicFunctions',
                namespaces=ns)
            oi_debug_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:IntrinsicFunctions',
                namespaces=ns)
            if oi_debug_x86 is not None and oi_debug_x64 is not None:
                if 'true' in oi_debug_x86.text and 'true' in oi_debug_x64.text:
                    debug_flags += ' /Oi'
            oi_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:IntrinsicFunctions',
                namespaces=ns)
            oi_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:IntrinsicFunctions',
                namespaces=ns)
            if oi_release_x86 is not None and oi_release_x64 is not None:
                if 'true' in oi_release_x86.text and 'true' in oi_release_x64.text:
                    release_flags += ' /Oi'

            # RuntimeTypeInfo
            gr_debug_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
                namespaces=ns)
            gr_debug_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
                namespaces=ns)
            if gr_debug_x64 is not None and gr_debug_x86 is not None:
                if 'false' in gr_debug_x64.text and gr_debug_x86.text:
                    debug_flags += ' /GR-'
                elif 'true' in gr_debug_x64.text and gr_debug_x86.text:
                    debug_flags += ' /GR'
            else:
                print("No RuntimeTypeInfo option.")
            gr_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
                namespaces=ns)
            gr_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
                namespaces=ns)
            if gr_release_x86 is not None and gr_release_x64 is not None:
                if 'false' in gr_release_x64.text and gr_release_x86.text:
                    release_flags += ' /GR-'
                elif 'true' in gr_release_x64.text and gr_release_x86.text:
                    release_flags += ' /GR'
            else:
                print("No RuntimeTypeInfo option.")

            # FunctionLevelLinking
            gy_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:FunctionLevelLinking',
                namespaces=ns)
            gy_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:FunctionLevelLinking',
                namespaces=ns)
            if 'true' in gy_release_x86.text and gy_release_x64.text:
                release_flags += ' /Gy'
            else:
                print("No FunctionLevelLinking option for release.")

            # GenerateDebugInformation
            zi_debug_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:Link/ns:GenerateDebugInformation',
                namespaces=ns)
            zi_debug_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:Link/ns:GenerateDebugInformation',
                namespaces=ns)
            if 'true' in zi_debug_x86.text and zi_debug_x64.text:
                debug_flags += ' /Zi'
            else:
                print("No GenerateDebugInformation option for debug.")

            zi_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:Link/ns:GenerateDebugInformation',
                namespaces=ns)
            zi_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:Link/ns:GenerateDebugInformation',
                namespaces=ns)
            if 'true' in zi_release_x86.text and zi_release_x64.text:
                release_flags += ' /Zi'
            else:
                print("No GenerateDebugInformation option for release.")

            # ExceptionHandling
            ehs_debug_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:ExceptionHandling',
                namespaces=ns)
            ehs_debug_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:ExceptionHandling',
                namespaces=ns)
            if ehs_debug_x86 is not None and ehs_debug_x64 is not None:
                if 'false' in ehs_debug_x86.text and ehs_debug_x64.text:
                    print("No ExceptionHandling option for debug.")
            else:
                debug_flags += ' /EHsc'
            ehs_release_x86 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:ExceptionHandling',
                namespaces=ns)
            ehs_release_x64 = tree.find(
                '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:ExceptionHandling',
                namespaces=ns)
            if ehs_release_x86 is not None and ehs_release_x64 is not None:
                if 'false' in ehs_release_x86.text and ehs_release_x64.text:
                    print("No ExceptionHandling option for release.")
            else:
                release_flags += ' /EHsc'

            # Write FLAGS in CMake
            if release_flags != '':
                cmakelist.write('set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}' + release_flags + '")\n')
            if debug_flags != '':
                cmakelist.write('set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}' + debug_flags + '")\n')
            print(OKBLUE + 'Release FLAGS found = ' + release_flags)
            print('Debug   FLAGS found = ' + debug_flags + ENDC)

            """
            Files
            """
            cmakelist.write('\nfile(GLOB SRC_FILES\n')
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
                    print(OKBLUE + 'Additional Dependencies = ' + depend.text  + ENDC)
                    listdepends = depend.text
                    for d in listdepends.split(';'):
                        if d != '%(AdditionalDependencies)':
                            cmakelist.write(d + ' ')
            except IndexError:
                print(OKBLUE + 'No dependencies' + ENDC)
            cmakelist.write(')')

        finally:
            cmakelist.close()
    except OSError:
        print(FAIL + 'ERROR =' + ENDC + ' You have to precise \'file.vcxproj\' to use this script.\nType : ' + OKBLUE + './vcxprojtocmake.py -h ' + ENDC + 'for more help !' + ENDC)


if __name__ == "__main__":
    main(sys.argv[1:])
