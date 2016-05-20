#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import etree
import ntpath as path
import os

############ RECUPERATION VCXPROJ #############

# TODO Prévoir l'entrée du fichier .vcxproj
tree = etree.parse("../corealpi/platform/msvc/vc2015/core.vcxproj")
ns = {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'}

############ GENERATION CMAKE #############

cmakelist = open('CMakeLists.txt', 'w')

"""
Project Name
"""
projectname = tree.xpath('//ns:RootNamespace', namespaces=ns)[0]
cmakelist.write('set(PROJECT_NAME ' + projectname.text + ')\n')

"""
Variables
"""
# Main Dir
# TODO Define root of project
root = "../../../"
cmakelist.write('set(MAIN_DIR ' + root + ')\n')

# Cpp Dir
cppfiles = tree.xpath('//ns:ClCompile', namespaces=ns)
cpp_path = []
for cpp in cppfiles:
    if cpp.get('Include') is not None:
        cxx = str(cpp.get('Include'))
        cpp_path.append(cxx)
cmakelist.write('set(CPP_DIR ' + os.path.commonprefix(cpp_path).replace('\\', '/') + '\n')

# Headers Dir
headerfiles = tree.xpath('//ns:ClInclude', namespaces=ns)
header_path = []
for header in headerfiles:
    h = str(header.get('Include'))
    header_path.append(h)
cmakelist.write('set(HEADER_DIR ' + os.path.commonprefix(header_path).replace('\\', '/') + '\n\n')
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
for ref in references:
    reference = str(ref.get('Include'))

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
cmakelist.write('    ${CPP_DIR}/src/*.cpp\n')
cmakelist.write('    ${HEADER_DIR}/src/*.h\n')
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
