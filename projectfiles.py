# --*- coding: utf-8 -*-

import message as msg

class ProjectFiles(object):
    c_folder_nb = 1
    h_folder_nb = 1

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.cppfiles = self.tree.xpath('//ns:ClCompile', namespaces=self.ns)
        self.headerfiles = self.tree.xpath('//ns:ClInclude', namespaces=self.ns)

    # TODO : put this method in projectvariables file
    def write_variables(self):
        # Cpp Dir
        known_cpp = []
        ProjectFiles.c_folder_nb = 1
        self.cmake.write('# Folders files\n')
        for cpp in self.cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in known_cpp:
                    known_cpp.append(current_cpp)
                    self.cmake.write('set(CPP_DIR_' + str(ProjectFiles.c_folder_nb) + ' ' + current_cpp + ')\n')
                    ProjectFiles.c_folder_nb += 1

        # Headers Dir
        known_headers = []
        ProjectFiles.h_folder_nb = 1
        for header in self.headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in known_headers:
                known_headers.append(current_header)
                self.cmake.write('set(HEADER_DIR_' + str(ProjectFiles.h_folder_nb) + ' ' + current_header + ')\n')
                ProjectFiles.h_folder_nb += 1

    def write_files(self):
        """
        Add directory variables to SRC_FILES
        """
        # Add files to project
        # TODO Glob Recurse for files.
        self.cmake.write('################ Files ################\n'
                         '#   --   Add files to project.   --   #\n'
                         '#######################################\n\n')
        self.cmake.write('file(GLOB SRC_FILES\n')
        c = 1
        while c < ProjectFiles.c_folder_nb:
            self.cmake.write('    ${CPP_DIR_' + str(c) + '}/*.cpp\n')
            c += 1
        h = 1
        while h < ProjectFiles.h_folder_nb:
            self.cmake.write('    ${HEADER_DIR_' + str(h) + '}/*.h\n')
            h += 1
        self.cmake.write(')\n\n')

    def add_additional_code(self, file_to_add):
        if file_to_add != '':
            try:
                fc = open(file_to_add, 'r')
                self.cmake.write('############# Additional Code #############\n')
                self.cmake.write('# Provides from external file.            #\n')
                self.cmake.write('###########################################\n\n')
                for line in fc:
                    self.cmake.write(line)
                fc.close()
                self.cmake.write('\n')
                msg.send('File of Code is added = ' + file_to_add, 'warn')
            except OSError:
                msg.send('Wrong data file ! Code was not added, please verify file name or path !', 'error')

    def add_artefact(self):
        """
        Library and Executable
        """
        configurationtype = self.tree.find('//ns:ConfigurationType', namespaces=self.ns)
        if configurationtype.text == 'DynamicLibrary':
            self.cmake.write('# Add library to build.\n')
            self.cmake.write('add_library(${PROJECT_NAME} SHARED\n')
            msg.send('CMake will build a SHARED Library.', '')
        elif configurationtype.text == 'StaticLibrary':
            self.cmake.write('# Add library to build.\n')
            self.cmake.write('add_library(${PROJECT_NAME} STATIC\n')
            msg.send('CMake will build a STATIC Library.', '')
        else:
            self.cmake.write('# Add executable to build.\n')
            self.cmake.write('add_executable(${PROJECT_NAME} \n')
            msg.send('CMake will build an EXECUTABLE.', '')
        self.cmake.write('   ${SRC_FILES}\n')
        self.cmake.write(')\n\n')