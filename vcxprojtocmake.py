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
        print(FAIL + message + ENDC)
    elif status == 'ok':
        print(OK + message + ENDC)
    else:
        print(message)

def main():
    """
    Main : verify if input_proj can be parse.
    """
    try:
        input_proj = ''
        parser = argparse.ArgumentParser(description='Convert file.vcxproj to CMakelists.txt')
        parser.add_argument('-p', help='absolute or relative path of a file.vcxproj')
        args = parser.parse_args()
        if args.p is not None:
            file_extension = os.path.splitext('/path/to/somefile.ext')
            if file_extension == '.vcxproj':
                input_proj = args.p
                msg('--project=' + args.p, '')

        """
        Constant Parameter
        ----------
        > Uncomment following line to use this script without parameters
        """
        # input_proj = '../corealpi/platform/msvc/vc2015/elec.vcxproj'

        get_xml_data(input_proj)
    except argparse.ArgumentError:
        sys.exit()

def get_xml_data(input_proj):
    """
    Get xml data from vcxproj
    :param input_proj: vcxproj file
    """

    # TODO : get Namespaces by parsing :param tree
    try:
        tree = etree.parse(input_proj)
        ns = {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        generate_cmake(tree, ns)
    except OSError:
        msg('.vcxproj file can not be import. Please verify path you give !', 'error')

def define_flags(tree, ns, cmake):
    """
    Define all flags inside project for Release and Debug Target.
    :param tree: vcxproj tree
    :param ns: namespace to use
    :param cmake: CMakeLists to write
    """

    # TODO : see if below can be refactor
    # TODO : get Conditions before for PropertyGroup
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

    if release_flags != '':
        msg('Release FLAGS found = ' + release_flags, 'ok')
        cmake.write('set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}' + release_flags + '")\n')
    if debug_flags != '':
        msg('Debug   FLAGS found = ' + debug_flags, 'ok')
        cmake.write('set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}' + debug_flags + '")\n')

def set_macro_definition(tree, ns, cmake):
    """
    Definitions : get Macro definitions.
    """
    preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
    cmake.write('add_definitions(\n')
    for preproc in preprocessor.text.split(";"):
        if preproc != '%(PreprocessorDefinitions)':
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
    cmake.write('option(BUILD_DEPENDS \n' +
    '   "Point to CMakeLists of other projects" \n' +
    '   ON \n' +
    ')\n\n')
    cmake.write('# Dependencies : disable BUILD_DEPENDS to link with lib already build.\n')
    cmake.write('if(BUILD_DEPENDS)\n')
    for ref in references:
        reference = str(ref.get('Include'))
        cmake.write(
            '   add_subdirectory(platform/cmake/' + os.path.splitext(path.basename(reference))[0] + ')\n')
    cmake.write('else()\n')
    for ref in references:
        reference = str(ref.get('Include'))
        cmake.write('   link_directories(dependencies/' + os.path.splitext(path.basename(reference))[
            0] + '/build/\n')
    cmake.write('endif()\n\n')

def link_dependencies(tree, ns, cmake):
    """
    Link : Add command to link dependencies to project.
    """
    references = tree.xpath('//ns:ProjectReference', namespaces=ns)
    cmake.write('target_link_libraries(${PROJECT_NAME} ')
    for ref in references:
        reference = str(ref.get('Include'))
        cmake.write(os.path.splitext(path.basename(reference))[0] + ' ')
        message = 'External librairies : ' + os.path.splitext(path.basename(reference))[0]
        msg(message, 'ok')
    try:
        if tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0] is not None:
            depend = tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0]
            msg('Additional Dependencies = ' + depend.text, 'ok')
            listdepends = depend.text
            for d in listdepends.split(';'):
                if d != '%(AdditionalDependencies)':
                    cmake.write(d + ' ')
    except IndexError:
        msg('No dependencies', '')

    cmake.write(')')

def define_variable(tree, ns, cmake):
    """
    Variable : define main variables in CMakeLists.
    :return header and cpp folder founds.
    """
    # CMake Minimum required.
    cmake.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

    # Project Name
    projectname = tree.xpath('//ns:RootNamespace', namespaces=ns)[0]
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
                cmake.write('set(CPP_DIR_' + str(cpp_nb) + ' ' + current_cpp + '\n')
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
            cmake.write('set(HEADER_DIR_' + str(header_nb) + ' ' + current_header + '\n')
            header_nb += 1

    # Project Definition
    cmake.write('\n')
    cmake.write('project(${PROJECT_NAME} CXX)\n\n')
    return header_nb, cpp_nb

def add_recursefiles(cmake, header_nb, cpp_nb):
    """
    Add directory variables to SRC_FILES
    :param header_nb: Number of header directory found.
    :param cpp_nb: Number of cpp directory found.
    :param cmake: CMakeLists to write
    """

    # Glob Recurse for files.
    cmake.write('\nfile(GLOB SRC_FILES\n')
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
        cmake.write('add_library(${PROJECT_NAME} SHARED\n')
    elif configurationtype.text == 'StaticLibrary':
        cmake.write('add_library(${PROJECT_NAME} STATIC\n')
    else:
        cmake.write('add_executable(${PROJECT_NAME} \n')
    cmake.write('   ${SRC_FILES}\n')
    cmake.write(')\n\n')

def generate_cmake(tree, ns):
    """
    :param tree: vcxproj tree
    :param ns: namespace to use
    """

    cmake = open('CMakeLists.txt', 'w')

    """
        Variables
    """
    header_nb, cpp_nb = define_variable(tree, ns, cmake)

    """
        Definitions
    """
    set_macro_definition(tree, ns, cmake)

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

if __name__ == "__main__":
    main()
