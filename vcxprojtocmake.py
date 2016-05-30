#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import etree
import ntpath as path
import sys, argparse, os

"""
Default Variable
"""

def msg(message, status):
    FAIL = ''
    OK = ''
    ENDC = ''

    if os.name == 'posix':
        FAIL += '\033[91m'
        OK += '\033[34m'
        ENDC += '\033[0m'
    if status == 'error':
        print('ERR  : ' + FAIL + message + ENDC)
    elif status == 'ok':
        print('OK   : ' + OK + message + ENDC)
    else:
        print('INFO : ' + message)

def main():
    """
    Main : verify if input_proj can be parse.
    """
    try:
        input_proj = ''
        output = ''
        filecode = ''
        parser = argparse.ArgumentParser(description='Convert file.vcxproj to CMakelists.txt')
        parser.add_argument('-p', help='absolute or relative path of a file.vcxproj')
        parser.add_argument('-o', help='define output. Ex: "../../platform/cmake/"')
        parser.add_argument('-I', help='import cmake filecode from text to your final CMakeLists.txt')
        args = parser.parse_args()
        if args.p is not None:
            file_path = os.path.splitext(args.p)
            if file_path[1] == '.vcxproj':
                input_proj = args.p
                msg('Project to convert = ' + args.p, '')
        if args.o is not None:
            if os.path.exists(args.o):
                output = args.o
                print('Sortie = ' + args.o)
            else:
                msg('This path does not exist. CMakeList will be generated in current directory.', 'error')
        if args.I is not None:
            filecode = args.I

        """
        Constant Parameter
        ----------
        > Uncomment following line to use this script without parameters
        """
        # input_proj = '../path/to/my.vcxproj'

        create_data(input_proj, output, filecode)
    except argparse.ArgumentError:
        sys.exit()

def create_data(input_proj, output, filecode):
    """
    Get xml data from vcxproj
    :param input_proj: vcxproj file
    :param output: path for CMakeLists.txt
    :param filecode: add additional code to your CMakeLists.txt
    """

    try:
        tree = etree.parse(input_proj)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        generate_cmake(tree, ns, output, filecode)
    except OSError:
        msg('.vcxproj file can not be import. Please, verify you have rights to access this directory !', 'error')
    except etree.XMLSyntaxError:
        msg('This file is not a file.vcxproj or xml is broken !', 'error')

def generate_cmake(tree, ns, output, filecode):
    """
    :param tree: vcxproj tree
    :param ns: namespace to use
    :param output: path for CMakeLists.txt
    :param filecode: add additional code to your CMakeLists.txt
    """

    """
    Constant Parameter
    ----------
    > Uncomment following line to use this script without parameters
    """
    # output = '../../platform/cmake/'

    if output is None:
        msg('CMakeLists will be build in current directory.', 'ok')
    else:
        msg('CmakeLists.txt will be build in : ' + output, 'ok')
    cmakelists = output + 'CMakeLists.txt'
    cmake = open(cmakelists, 'w')

    """
        Variables
    """
    header_nb, cpp_nb = define_variable(tree, ns, cmake)

    """
        Definitions
    """
    set_macro_definition(tree, ns, cmake)

    """
        General and Additional Code
    """
    set_output(tree, ns, cmake)
    add_additional_code(cmake, filecode)

    """
        Dependencies
    """
    set_dependencies(tree, ns, cmake)

    """
    Flags
    """
    define_flags(tree, ns, cmake)

    """
    Files
    """
    add_recursefiles(cmake, header_nb, cpp_nb)

    """
    Library and Executable
    """
    create_artefact(tree, ns, cmake)

    """
    Link and dependencies
    """
    link_dependencies(tree, ns, cmake)

    cmake.close()

def add_additional_code(cmake, filecode):
    """
    :param cmake: CMakeLists to write
    :param filecode: add additional code to your CMakeLists.txt
    :return:
    """
    print('Fichier = ' + filecode)
    fc = open(filecode, 'r')
    cmake.write('# Additional Code \n')
    for line in fc:
        cmake.write(line)
    fc.close()


def define_variable(tree, ns, cmake):
    """
    Variable : define main variables in CMakeLists.
    :return header and cpp folder founds.
    """
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
    path_debug_x86 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
        namespaces=ns)
    output_deb_x86 = path_debug_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
    msg('Output Debug x86 = ' + output_deb_x86, 'ok')
    cmake.write('set(OUTPUT_DEBUG_X86 ' + output_deb_x86 + ')\n')
    path_debug_x64 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
        namespaces=ns)
    output_deb_x64 = path_debug_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
    msg('Output Debug x64 = ' + output_deb_x64, 'ok')
    cmake.write('set(OUTPUT_DEBUG_X64 ' + output_deb_x64 + ')\n')
    path_release_x86 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:OutDir',
        namespaces=ns)
    output_rel_x86 = path_release_x86.text.replace('$(ProjectDir)', '').replace('\\', '/')
    msg('Output Release x86 = ' + output_rel_x86, 'ok')
    cmake.write('set(OUTPUT_REL_X86 ' + output_rel_x86 + ')\n')
    path_release_x64 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:OutDir',
        namespaces=ns)
    output_rel_x64 = path_release_x64.text.replace('$(ProjectDir)', '').replace('\\', '/')
    msg('Output Release x64 = ' + output_rel_x64, 'ok')
    cmake.write('set(OUTPUT_REL_X64 ' + output_rel_x64 + ')\n')

    # Project Definition
    cmake.write('\n')
    cmake.write('# Define Project.\n')
    cmake.write('project(${PROJECT_NAME} CXX)\n\n')
    return header_nb, cpp_nb

def set_output(tree, ns, cmake):
    """
    Set output for each target
    """
    cmake.write('# Define Output Debug of artefacts \n')
    if tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
        namespaces=ns) is not None and tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
        namespaces=ns) is not None:
        cmake.write('if(CMAKE_BUILD_TYPE EQUAL "Debug")\n')
        cmake.write('  if(x64)\n')
        cmake.write('    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}${OUTPUT_DEBUG_X64})\n')
        cmake.write('  else()\n')
        cmake.write('    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}${OUTPUT_DEBUG_X86})\n')
        cmake.write('  endif()\n')
        cmake.write('endif()\n')
    cmake.write('# Define Output Release of artefacts \n')
    if tree.find(
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:OutDir',
            namespaces=ns) is not None and tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:OutDir',
        namespaces=ns) is not None:
        cmake.write('if(CMAKE_BUILD_TYPE EQUAL "Release")\n')
        cmake.write('  if(x64)\n')
        cmake.write('    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}${OUTPUT_RELEASE_X64})\n')
        cmake.write('  else()\n')
        cmake.write('    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_BINARY_DIR}${OUTPUT_RELEASE_X86})\n')
        cmake.write('  endif()\n')
        cmake.write('endif()\n')
    cmake.write('\n')

def define_flags(tree, ns, cmake):
    """
    Define all FLAGS inside project for Release and Debug Target.
    :param tree: vcxproj tree
    :param ns: namespace to use
    :param cmake: CMakeLists to write
    """

    # TODO : add condition for MSVC
    # TODO : add -std=c++11
    release_flags = ''
    debug_flags = ''

    # Warning
    warning = tree.xpath('//ns:WarningLevel', namespaces=ns)[0]
    if warning.text != '':
        lvl = ' /W' + warning.text[-1:]
        debug_flags += lvl
        release_flags += lvl
        msg('Warning : ' + warning.text, 'ok')
    else:
        msg('No Warning level.', '')

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
            msg('WholeProgramOptimization for Debug', 'ok')
    else:
        msg('No WholeProgramOptimization for Debug', '')
    gl_release_x86 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:WholeProgramOptimization',
        namespaces=ns)
    gl_release_x64 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:WholeProgramOptimization',
        namespaces=ns)
    if gl_release_x86 is not None and gl_release_x64 is not None:
        if 'true' in gl_release_x86.text and 'true' in gl_release_x64.text:
            release_flags += ' /GL'
            msg('WholeProgramOptimization for Release', 'ok')
    else:
        msg('No WholeProgramOptimization for Release', '')

    # UseDebugLibraries
    md_debug_x86 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:UseDebugLibraries',
        namespaces=ns)
    md_debug_x64 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:UseDebugLibraries',
        namespaces=ns)
    if md_debug_x64 is not None and md_debug_x86 is not None:
        if 'true' in md_debug_x86.text and 'true' in md_debug_x64.text:
            debug_flags += ' /MD'
            msg('UseDebugLibrairies for Debug', 'ok')
    else:
        msg('No UseDebugLibrairies for Debug', '')
    md_release_x86 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:UseDebugLibraries',
        namespaces=ns)
    md_release_x64 = tree.find(
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:UseDebugLibraries',
        namespaces=ns)
    if md_release_x86 is not None and md_release_x64 is not None:
        if 'true' in md_release_x86.text and 'true' in md_release_x64.text:
            release_flags += ' /MD'
            msg('UseDebugLibrairies for Release', 'ok')
    else:
        msg('No UseDebugLibrairies for Release', '')

    # RuntimeLibrary
    mdd_debug_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:RuntimeLibrary',
        namespaces=ns)
    mdd_debug_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:RuntimeLibrary',
        namespaces=ns)
    if mdd_debug_x64 is not None and mdd_debug_x86 is not None:
        if 'MultiThreadedDebugDLL' in mdd_debug_x86.text and 'MultiThreadedDebugDLL' in mdd_debug_x64.text:
            debug_flags += ' /MDd'
            msg('RuntimeLibrary for Debug', 'ok')
    else:
        msg('No RuntimeLibrary for Debug', '')
    mdd_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:RuntimeLibrary',
        namespaces=ns)
    mdd_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:RuntimeLibrary',
        namespaces=ns)
    if mdd_release_x86 is not None and mdd_release_x64 is not None:
        if 'MultiThreadedDebugDLL' in mdd_release_x86.text and 'MultiThreadedDebugDLL' in mdd_release_x64.text:
            release_flags += ' /MDd'
            msg('RuntimeLibrary for Release', 'ok')
    else:
        msg('No RuntimeLibrary for Release', '')

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
            msg('Optimization for Debug', 'ok')
    else:
        msg('No Optimization for Debug', '')
    opt_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:Optimization',
        namespaces=ns)
    opt_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:Optimization',
        namespaces=ns)
    if opt_release_x86 is not None and opt_release_x64 is not None:
        if 'MaxSpeed' in opt_release_x64.text and 'MaxSpeed' in opt_release_x86.text:
            release_flags += ' /O2'
            msg('Optimization for Release', 'ok')
    else:
        msg('No Optimization for Release', '')

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
            msg('IntrinsicFunctions for Debug', 'ok')
    else:
        msg('No IntrinsicFunctions for Debug', '')
    oi_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:IntrinsicFunctions',
        namespaces=ns)
    oi_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:IntrinsicFunctions',
        namespaces=ns)
    if oi_release_x86 is not None and oi_release_x64 is not None:
        if 'true' in oi_release_x86.text and 'true' in oi_release_x64.text:
            release_flags += ' /Oi'
            msg('IntrinsicFunctions for Release', 'ok')
    else:
        msg('No IntrinsicFunctions for Release', '')

    # RuntimeTypeInfo
    gr_debug_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
        namespaces=ns)
    gr_debug_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
        namespaces=ns)
    if gr_debug_x64 is not None and gr_debug_x86 is not None:
        if 'true' in gr_debug_x64.text and gr_debug_x86.text:
            debug_flags += ' /GR'
            msg('RuntimeTypeInfo for Debug', 'ok')
    else:
        msg('No RuntimeTypeInfo for Debug', '')
    gr_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
        namespaces=ns)
    gr_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:RuntimeTypeInfo',
        namespaces=ns)
    if gr_release_x86 is not None and gr_release_x64 is not None:
        if 'true' in gr_release_x64.text and gr_release_x86.text:
            release_flags += ' /GR'
            msg('RuntimeTypeInfo for Release', 'ok')
    else:
        msg('No RuntimeTypeInfo for Release', '')

    # FunctionLevelLinking
    gy_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:FunctionLevelLinking',
        namespaces=ns)
    gy_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:FunctionLevelLinking',
        namespaces=ns)
    if gy_release_x86 is not None and gy_release_x64 is not None:
        if 'true' in gy_release_x86.text and 'true' in gy_release_x64.text:
            release_flags += ' /Gy'
            msg('FunctionLevelLinking for release.', 'ok')
    else:
        msg('No FunctionLevelLinking for release.', '')

    # GenerateDebugInformation
    zi_debug_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:Link/ns:GenerateDebugInformation',
        namespaces=ns)
    zi_debug_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:Link/ns:GenerateDebugInformation',
        namespaces=ns)
    if zi_debug_x86 is not None and zi_debug_x64 is not None:
        if 'true' in zi_debug_x86.text and zi_debug_x64.text:
            debug_flags += ' /Zi'
            msg('GenerateDebugInformation for debug.', 'ok')
    else:
        msg('No GenerateDebugInformation for debug.', '')

    zi_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:Link/ns:GenerateDebugInformation',
        namespaces=ns)
    zi_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:Link/ns:GenerateDebugInformation',
        namespaces=ns)
    if zi_release_x86 is not None and zi_release_x64 is not None:
        if 'true' in zi_release_x86.text and zi_release_x64.text:
            release_flags += ' /Zi'
            msg('GenerateDebugInformation for release.', 'ok')
    else:
        msg('No GenerateDebugInformation for release.', '')

    # ExceptionHandling
    ehs_debug_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]/ns:ClCompile/ns:ExceptionHandling',
        namespaces=ns)
    ehs_debug_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]/ns:ClCompile/ns:ExceptionHandling',
        namespaces=ns)
    if ehs_debug_x86 is not None and ehs_debug_x64 is not None:
        if 'false' in ehs_debug_x86.text and ehs_debug_x64.text:
            msg('No ExceptionHandling for debug.', '')
    else:
        debug_flags += ' /EHsc'
        msg('ExceptionHandling for debug.', 'ok')
    ehs_release_x86 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]/ns:ClCompile/ns:ExceptionHandling',
        namespaces=ns)
    ehs_release_x64 = tree.find(
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]/ns:ClCompile/ns:ExceptionHandling',
        namespaces=ns)
    if ehs_release_x86 is not None and ehs_release_x64 is not None:
        if 'false' in ehs_release_x86.text and ehs_release_x64.text:
            msg('No ExceptionHandling option for release.', '')
    else:
        release_flags += ' /EHsc'
        msg('ExceptionHandling for release.', 'ok')

    if debug_flags != '':
        msg('Debug   FLAGS found = ' + debug_flags, 'ok')
        cmake.write('# Flags for target "Debug"\n')
        cmake.write('set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}' + debug_flags + '")\n')
    else:
        msg('No Debug   FLAGS found', '')
    if release_flags != '':
        msg('Release FLAGS found = ' + release_flags, 'ok')
        cmake.write('# Flags for target "Release"\n')
        cmake.write('set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}' + release_flags + '")\n')
    else:
        msg('No Release FLAGS found', '')

def set_macro_definition(tree, ns, cmake):
    """
    Definitions : get Macro definitions.
    """
    preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
    cmake.write('# Definition of Macros and/or Flags\n')
    cmake.write('add_definitions(\n')
    for preproc in preprocessor.text.split(";"):
        if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
            cmake.write('   -D' + preproc + ' \n')
            # Unicode
    u = tree.find("//ns:CharacterSet", namespaces=ns)
    if 'Unicode' in u.text:
        cmake.write('   -DUNICODE\n')
        cmake.write('   -D_UNICODE\n')
    cmake.write(')\n\n')

def set_dependencies(tree, ns, cmake):
    """
    Dependencies : Add subdirectories or link directories for external libraries.
    """
    references = tree.xpath('//ns:ProjectReference', namespaces=ns)
    if references:
        cmake.write('# Add Dependencies of project.\n# Choose if you want build other CMake project or link with directories.\n')
        cmake.write('option(BUILD_DEPENDS \n' +
        '   "Point to CMakeLists of other projects" \n' +
        '   ON \n' +
        ')\n\n')
        cmake.write('# Dependencies : disable BUILD_DEPENDS to link with lib already build.\n')
        cmake.write('if(BUILD_DEPENDS)\n')
        for ref in references:
            reference = str(ref.get('Include'))
            cmake.write(
                '   add_subdirectory(platform/cmake/' + os.path.splitext(path.basename(reference))[0] +
                ' ${CMAKE_BINARY_DIR}/' + os.path.splitext(path.basename(reference))[0] + ')\n')
        cmake.write('else()\n')
        for ref in references:
            reference = str(ref.get('Include'))
            cmake.write('   link_directories(dependencies/' + os.path.splitext(path.basename(reference))[
                0] + '/build/)\n')
        cmake.write('endif()\n\n')
    else:
        msg('No link needed.', '')

def link_dependencies(tree, ns, cmake):
    """
    Link : Add command to link dependencies to project.
    """
    references = tree.xpath('//ns:ProjectReference', namespaces=ns)
    if references:
        cmake.write('# Link with other dependencies.\n')
        cmake.write('target_link_libraries(${PROJECT_NAME} ')
        for ref in references:
            reference = str(ref.get('Include'))
            cmake.write(os.path.splitext(path.basename(reference))[0] + ' ')
            message = 'External librairies : ' + os.path.splitext(path.basename(reference))[0]
            msg(message, 'ok')
        cmake.write(')\n')
        try:
            if tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0] is not None:
                depend = tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0]
                if depend.text != '%(AdditionalDependencies)':
                    msg('Additional Dependencies = ' + depend.text, 'ok')
                listdepends = depend.text
                windepends = []
                for d in listdepends.split(';'):
                    print('ADDITIONAL DEPENDENCIES = ' + d)
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            windepends.append(d)
                        #cmake.write(d + ' ')
                print(windepends)
                if windepends is not None:
                    cmake.write('if(MSVC)\n')
                    cmake.write('   target_link_libraries(${PROJECT_NAME} ')
                    for dep in windepends:
                        cmake.write(dep + ' ')
                    cmake.write(')\n')
                    cmake.write('endif(MSVC)\n')
            cmake.write(')')
        except IndexError:
            msg('No dependencies', '')
    else:
        msg('No dependencies.', '')

def add_recursefiles(cmake, header_nb, cpp_nb):
    """
    Add directory variables to SRC_FILES
    :param header_nb: Number of header directory found.
    :param cpp_nb: Number of cpp directory found.
    :param cmake: CMakeLists to write
    """

    # Glob Recurse for files.
    cmake.write('\n# Add files to project.\n')
    cmake.write('file(GLOB SRC_FILES\n')
    c = 1
    while c < cpp_nb:
        cmake.write('    ${CPP_DIR_' + str(c) + '}/*.cpp\n')
        c += 1
    h = 1
    while h < header_nb:
        cmake.write('    ${HEADER_DIR_' + str(h) + '}/*.h\n')
        h += 1
    cmake.write(')\n\n')

def create_artefact(tree, ns, cmake):
    """
    Library and Executable
    """
    configurationtype = tree.find('//ns:ConfigurationType', namespaces=ns)
    if configurationtype.text == 'DynamicLibrary':
        cmake.write('# Add library to build.\n')
        cmake.write('add_library(${PROJECT_NAME} SHARED\n')
    elif configurationtype.text == 'StaticLibrary':
        cmake.write('# Add library to build.\n')
        cmake.write('add_library(${PROJECT_NAME} STATIC\n')
    else:
        cmake.write('# Add executable to build.\n')
        cmake.write('add_executable(${PROJECT_NAME} \n')
    cmake.write('   ${SRC_FILES}\n')
    cmake.write(')\n\n')

if __name__ == "__main__":
    main()
