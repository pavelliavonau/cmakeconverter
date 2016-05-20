#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import etree
import ntpath as path
import os
import sys

# TODO Prévoir l'entrée du fichier .vcxproj
tree = etree.parse("core.vcxproj")
ns = {'ns':'http://schemas.microsoft.com/developer/msbuild/2003'}

confs = tree.xpath('//ns:Configuration', namespaces=ns)
unique_conf = [None] * len(confs)
for conf in confs:
    if conf.text not in unique_conf:
        print('Target = ' + conf.text)
        unique_conf.append(conf.text)

projectname = tree.xpath('//ns:RootNamespace', namespaces=ns)[0]
print('Project Name = ' + projectname.text)

configurationtype = tree.find('//ns:ConfigurationType', namespaces=ns)
print('Configuration Type = ' + configurationtype.text)

preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
print('Preprocessor = ' + preprocessor.text)

depend = tree.xpath('//ns:AdditionalDependencies', namespaces=ns)[0]
print('Additional Dependencies = ' + depend.text)

cppfiles = tree.xpath('//ns:ClCompile', namespaces=ns)
cpp_path = []
for cpp in cppfiles:
    if cpp.get('Include') is not None:
        cxx = str(cpp.get('Include'))
        print('Fichier = ' + cxx)
        cpp_path.append(cxx)

headerfiles = tree.xpath('//ns:ClInclude', namespaces=ns)
header_path = []
for header in headerfiles:
    h = str(header.get('Include'))
    print('Header = ' + h)
    header_path.append(h)
print(os.path.commonprefix(header_path))

references = tree.xpath('//ns:ProjectReference', namespaces=ns)
for ref in references:
    reference = str(ref.get('Include'))
    print(os.path.splitext(path.basename(reference))[0])

print(os.path.dirname(os.path.realpath('../corealpi/platform/msvc/vc2015/elec.vcxproj')))

# TODO Définir le dossier racine du projet
root = "../../../"

"""
############ GENERATION CMAKE #############
"""
cmakelist = open('CMakeLists.txt', 'w')

"""
Project Name and Variables
"""
cmakelist.write('set(PROJECT_NAME ' + projectname.text + ')\n')
cmakelist.write('set(MAIN_DIR ' + root + ')\n\n')
cmakelist.write('project(${PROJECT_NAME} CXX)\n\n')

"""
Definitions
"""
cmakelist.write('add_definitions(\n')
for preproc in preprocessor.text.split(";"):
    if preproc != '%(PreprocessorDefinitions)':
        cmakelist.write('-D' + preproc + ' \n')
cmakelist.write(')\n\n')

"""
Dependencies
"""
cmakelist.write('# Dépendances\nif(BUILD_DEPENDS)\n')
for ref in references:
    reference = str(ref.get('Include'))
    cmakelist.write('   add_subdirectory(${COREALPI_DIR}/platform/cmake/' + os.path.splitext(path.basename(reference))[0] + ')\n')
cmakelist.write('else()\n')
for ref in references:
    reference = str(ref.get('Include'))
    cmakelist.write('   link_directories(${COREALPI_DIR}/dependencies/' + os.path.splitext(path.basename(reference))[0] + '/build/${CMAKE_BUILD_TYPE})\n')
cmakelist.write('endif()\n\n')

"""
Librarie
"""
if configurationtype.text == 'DynamicLibrary':
    cmakelist.write('add_library(${PROJECT_NAME} SHARED\n')
elif configurationtype.text == 'StaticLibrary':
    cmakelist.write('add_library(${PROJECT_NAME} STATIC\n')
else:
    cmakelist.write('add_executable(${PROJECT_NAME} \n')
cmakelist.write('   ' + os.path.commonprefix(header_path) + '*.h\n')
cmakelist.write('   ' + os.path.commonprefix(cpp_path) + '*.cpp\n')
cmakelist.write(')')