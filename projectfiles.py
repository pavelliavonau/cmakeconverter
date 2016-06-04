# --*- coding: utf-8 -*-

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
        global c_folder_nb
        global h_folder_nb

        # Cpp Dir
        known_cpp = []
        c_folder_nb = 1
        for cpp in self.cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                current_cpp = '/'.join(cxx.split('\\')[0:-1])
                if current_cpp not in known_cpp:
                    known_cpp.append(current_cpp)
                    self.cmake.write('set(CPP_DIR_' + str(c_folder_nb) + ' ' + current_cpp + ')\n')
                    c_folder_nb += 1

        # Headers Dir
        known_headers = []
        h_folder_nb = 1
        for header in self.headerfiles:
            h = str(header.get('Include'))
            current_header = '/'.join(h.split('\\')[0:-1])
            if current_header not in known_headers:
                known_headers.append(current_header)
                self.cmake.write('set(HEADER_DIR_' + str(h_folder_nb) + ' ' + current_header + ')\n')
                h_folder_nb += 1

    def write_files(self):
        """
        Add directory variables to SRC_FILES
        """
        global c_folder_nb
        global h_folder_nb

        # Add files to project
        # TODO Glob Recurse for files.
        self.cmake.write('\n# Add files to project.\n')
        self.cmake.write('file(GLOB SRC_FILES\n')
        c = 1
        while c < c_folder_nb:
            self.cmake.write('    ${CPP_DIR_' + str(c) + '}/*.cpp\n')
            c += 1
        h = 1
        while h < h_folder_nb:
            self.cmake.write('    ${HEADER_DIR_' + str(h) + '}/*.h\n')
            h += 1
        self.cmake.write(')\n\n')
