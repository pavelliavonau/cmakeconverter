# -*- coding: utf-8 -*-

import os
import ntpath as path
import message as msg
import re

class Dependencies(object):
    """
    Dependencies : find and write dependencies of project, additionnal directories...
    """

    def __init__(self, data):
        self.cmake = data['cmake']
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.dependencies = data['dependencies']

    def write_include_dir(self):
        """
        Include Directories : Add include directories required for compilation.
        """
        incl_dir = self.tree.find('//ns:ItemGroup/ns:ClCompile/ns:AdditionalIncludeDirectories', namespaces=self.ns)
        if incl_dir is not None:
            self.cmake.write('# Include directories \n')
            inc_dir = incl_dir.text.replace('$(ProjectDir)', '')
            for i in inc_dir.split(';'):
                i = i.replace('\\', '/')
                i = re.sub(r'\$\((.+?)\)', r'$ENV{\1}', i)
                self.cmake.write('include_directories(' + i + ')\n')
                msg.send('Include Directories found : ' + i, 'warn')
            self.cmake.write('\n')
        else:
            msg.send('Include Directories not found for this project.', 'warn')

    def write_dependencies(self):
        """
        Dependencies : Add subdirectories or link directories for external libraries.
        """
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            self.cmake.write('################### Dependencies ##################\n'
                             '# Add Dependencies to project.                    #\n'
                             '###################################################\n\n')
            self.cmake.write('option(BUILD_DEPENDS \n' +
                        '   "Build other CMake project." \n' +
                        '   ON \n' +
                        ')\n\n')
            self.cmake.write('# Dependencies : disable BUILD_DEPENDS to link with lib already build.\n')
            if self.dependencies is None:
                self.cmake.write('if(BUILD_DEPENDS)\n')
                for ref in references:
                    reference = str(ref.get('Include'))
                    self.cmake.write(
                        '   add_subdirectory(platform/cmake/' + os.path.splitext(path.basename(reference))[0] +
                        ' ${CMAKE_BINARY_DIR}/' + os.path.splitext(path.basename(reference))[0] + ')\n')
            else:
                self.cmake.write('if(BUILD_DEPENDS)\n')
                d = 1
                for ref in self.dependencies:
                    self.cmake.write(
                        '   add_subdirectory(' + ref + ' ${CMAKE_BINARY_DIR}/lib' + str(d) + ')\n')
                    msg.send('Add manually dependencies : ' + ref + '. Will be build in "lib' + str(d) + '/" !', 'warn')
                    d += 1
            self.cmake.write('else()\n')
            for ref in references:
                reference = str(ref.get('Include'))
                self.cmake.write('   link_directories(dependencies/' + os.path.splitext(path.basename(reference))[
                    0] + '/build/)\n')
            self.cmake.write('endif()\n\n')
        else:
            msg.send('No link needed.', '')

    def link_dependencies(self):
        """
        Link : Add command to link dependencies to project.
        """
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            self.cmake.write('# Link with other dependencies.\n')
            self.cmake.write('target_link_libraries(${PROJECT_NAME} ')
            for ref in references:
                reference = str(ref.get('Include'))
                lib = os.path.splitext(path.basename(reference))[0]
                if lib == 'g3log':
                    lib += 'ger'
                self.cmake.write(lib + ' ')
                message = 'External librairy found : ' + os.path.splitext(path.basename(reference))[0]
                msg.send(message, '')
            self.cmake.write(')\n')
            try:
                if self.tree.xpath('//ns:AdditionalDependencies', namespaces=self.ns)[0] is not None:
                    depend = self.tree.xpath('//ns:AdditionalDependencies', namespaces=self.ns)[0]
                    listdepends = depend.text.replace('%(AdditionalDependencies)', '')
                    if listdepends != '':
                        msg.send('Additional Dependencies = ' + listdepends, 'ok')
                    windepends = []
                    for d in listdepends.split(';'):
                        if d != '%(AdditionalDependencies)':
                            if os.path.splitext(d)[1] == '.lib':
                                windepends.append(d)
                    if windepends is not None:
                        self.cmake.write('if(MSVC)\n')
                        self.cmake.write('   target_link_libraries(${PROJECT_NAME} ')
                        for dep in windepends:
                            self.cmake.write(dep + ' ')
                        self.cmake.write(')\n')
                        self.cmake.write('endif(MSVC)\n')
            except IndexError:
                msg.send('No dependencies', '')
        else:
            msg.send('No dependencies.', '')