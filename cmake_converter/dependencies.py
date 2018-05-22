#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017:
#   Matthieu Estrada, ttamalfor@gmail.com
#
# This file is part of (CMakeConverter).
#
# (CMakeConverter) is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# (CMakeConverter) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with (CMakeConverter).  If not, see <http://www.gnu.org/licenses/>.

"""
    Dependencies
    ============
     Manage directories and libraries of project dependencies
"""

import ntpath
import os
import re

from cmake_converter.data_files import get_vcxproj_data, get_xml_data
from cmake_converter.utils import write_property_of_settings, \
    get_global_project_name_from_vcxproj_file, cleaning_output, normalize_path, message


class Dependencies(object):
    """
        Class who find and write dependencies of project, additionnal directories...
    """

    def __init__(self, context):
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.dependencies = context['dependencies']
        self.deps = context['sln_deps']
        self.settings = context['settings']
        self.definition_groups = context['definition_groups']
        self.includes = context['includes']
        self.vcxproj_path = context['vcxproj_path']
        self.context = context

    def find_include_dir(self):
        """
        Write on "CMakeLists.txt" include directories required for compilation.

        """
        if not self.includes:
            message('Include Directories is not set.', '')
            return

        for setting in self.settings:
            incl_dir = self.tree.find(
                '{0}/ns:ClCompile/ns:AdditionalIncludeDirectories'.format(self.definition_groups[setting]),
                namespaces=self.ns
            )

            if incl_dir is not None:
                inc_dirs = self.get_additional_include_directories(incl_dir.text, setting, self.context)
                message('Include Directories found : {0}'.format(inc_dirs), 'warn')
            else:  # pragma: no cover
                message('Include Directories not found for this project.', 'warn')

    @staticmethod
    def write_include_directories(context, cmake_file):
        write_property_of_settings(cmake_file, context['settings'], context['sln_configurations_map'],
                                   'target_include_directories(${PROJECT_NAME} PRIVATE ', ')', 'inc_dirs')
        cmake_file.write('\n')

    @staticmethod
    def get_additional_include_directories(aid_text, setting, context):
        if not aid_text:
            return

        working_path = os.path.dirname(context['vcxproj_path'])
        inc_dir = aid_text.replace('$(ProjectDir)', './')
        inc_dir = inc_dir.replace(';%(AdditionalIncludeDirectories)', '')
        dirs = []
        for i in inc_dir.split(';'):
            i = normalize_path(working_path, i)
            i = re.sub(r'\$\((.+?)\)', r'$ENV{\1}', i)
            dirs.append(i)
        inc_dirs = ';'.join(dirs)
        context['settings'][setting]['inc_dirs'] = inc_dirs
        return inc_dirs

    @staticmethod
    def get_dependency_target_name(vs_project):
        """
        Return dependency of target

        :param vs_project: vcxproj
        :return:
        """
        # VS Project (.vcxproj)
        vcxproj = get_vcxproj_data(vs_project)
        project_name = get_global_project_name_from_vcxproj_file(vcxproj)
        if project_name:
            return project_name
        else:
            return os.path.splitext(ntpath.basename(vs_project))[0]

    def find_target_references(self):
        """
        Find references of project

        """

        references_found = []
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            for ref in references:
                if ref is None:
                    continue

                ref_inc = ref.get('Include')
                if ref_inc is None:
                    continue

                if ref_inc not in references_found:
                    references_found.append(ref_inc)

        self.context['target_references'] = references_found

    def write_target_references(self, cmake_file):
        if self.context['target_references']:
            cmake_file.write('add_dependencies(${PROJECT_NAME}')
            targets_dependencies = set()
            for ref_found in self.context['target_references']:
                project_name = self.get_dependency_target_name(os.path.join(os.path.dirname(self.vcxproj_path),
                                                                            ref_found))
                targets_dependencies.add(project_name)
                cmake_file.write(' {0}'.format(project_name))
            for dep in self.deps:
                if dep not in targets_dependencies:
                    cmake_file.write(' {0}'.format(dep))

            cmake_file.write(')\n\n')

    def write_dependencies(self, cmake_file):
        """
        Write on "CMakeLists.txt" subdirectories or link directories for external libraries.

        """
        if self.context['target_references']:
            cmake_file.write('################### Dependencies ##################\n'
                             '# Add Dependencies to project.                    #\n'
                             '###################################################\n\n')
            self.write_target_references(cmake_file)
            return  # TODO: looks like wrong code
            cmake_file.write(
                'option(BUILD_DEPENDS \n' +
                '   "Build other CMake project." \n' +
                '   ON \n' +
                ')\n\n'
            )
            cmake_file.write(
                '# Dependencies : disable BUILD_DEPENDS to link with lib already build.\n'
            )
            if self.dependencies is None:
                cmake_file.write('if(BUILD_DEPENDS)\n')
                for ref in references:
                    reference = str(ref.get('Include'))
                    path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                    cmake_file.write(
                        '   add_subdirectory(platform/cmake/%s ${CMAKE_BINARY_DIR}/%s)\n' % (
                            path_to_reference, path_to_reference
                        )
                    )
            else:
                cmake_file.write('if(BUILD_DEPENDS)\n')
                d = 1
                for ref in self.dependencies:
                    cmake_file.write(
                        '   add_subdirectory(%s ${CMAKE_BINARY_DIR}/lib%s)\n' % (ref, str(d)))
                    message(
                        'Add manually dependencies : %s. Will be build in "lib%s/" !' % (
                            ref, str(d)),
                        'warn'
                    )
                    d += 1
            cmake_file.write('else()\n')
            for ref in references:
                reference = str(ref.get('Include'))
                path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                cmake_file.write(
                    '   link_directories(dependencies/%s/build/)\n' % path_to_reference
                )
            cmake_file.write('endif()\n\n')
        else:  # pragma: no cover
            message('No link needed.', '')

    def find_target_additional_dependencies(self):
        # Additional Dependencies
        dependencies = self.tree.xpath('//ns:AdditionalDependencies', namespaces=self.ns)
        self.context['add_lib_deps'] = []
        if dependencies:
            list_depends = dependencies[0].text.replace('%(AdditionalDependencies)', '')
            if list_depends != '':
                message('Additional Dependencies = %s' % list_depends, 'ok')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            add_lib_dirs.append(d.replace('.lib', ''))
                self.context['add_lib_deps'] = add_lib_dirs
        else:  # pragma: no cover
            message('No dependencies.', '')

    def find_target_additional_library_directories(self):
        # Additional Library Directories
        additional_library_directories = self.tree.xpath('//ns:AdditionalLibraryDirectories', namespaces=self.ns)
        self.context['add_lib_dirs'] = []
        if additional_library_directories:
            list_depends = additional_library_directories[0].text.replace('%(AdditionalLibraryDirectories)', '')
            if list_depends != '':
                message('Additional Library Directories = %s' % list_depends, 'ok')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    d = d.strip()
                    if d != '':
                        add_lib_dirs.append(d)
                self.context['add_lib_dirs'] = add_lib_dirs
        else:  # pragma: no cover
            message('No dependencies.', '')

    def write_link_dependencies(self, cmake_file):
        """
        Write link dependencies of project.

        """

        if self.context['target_references']:
            cmake_file.write('# Link with other targets.\n')
            cmake_file.write('target_link_libraries(${PROJECT_NAME}')
            for reference in self.context['target_references']:
                path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                lib = self.get_dependency_target_name(os.path.join(os.path.dirname(self.vcxproj_path), reference))
                cmake_file.write(' ' + lib)
                msg = 'External library found : {0}'.format(path_to_reference)
                message(msg, '')
            cmake_file.write(')\n')

        if self.context['add_lib_deps']:
            cmake_file.write('# Link with other additional libraries.\n')
            cmake_file.write('target_link_libraries(${PROJECT_NAME}')
            for dep in self.context['add_lib_deps']:
                cmake_file.write(' ' + dep)
            cmake_file.write(')\n')

        if self.context['add_lib_dirs']:
            cmake_file.write('if(MSVC)\n')
            cmake_file.write('   target_link_libraries(${PROJECT_NAME}')
            for dep in self.context['add_lib_dirs']:
                cmake_file.write(' -LIBPATH:' + cleaning_output(dep))
            cmake_file.write(')\n')
            cmake_file.write('endif(MSVC)\n')

    def find_target_dependency_packages(self):
        """
        Other dependencies of project. Like nuget for example.

        """
        self.context['packages'] = []
        packages_xml = get_xml_data(os.path.join(os.path.dirname(self.vcxproj_path), 'packages.config'))
        # External libraries
        if packages_xml:
            extension = packages_xml['tree'].xpath('/packages/package')
            for ref in extension:
                package_id = ref.get('id')
                package_version = ref.get('version')
                self.context['packages'].append([package_id, package_version])

    def write_target_dependency_packages(self, cmake_file):
        for package in self.context['packages']:
            cmake_file.write('\nuse_package(${{PROJECT_NAME}} {0} {1})'.format(package[0], package[1]))
