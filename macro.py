# -*- coding: utf-8 -*-


class Macro(object):

    @staticmethod
    def write_macro(data):
        """
        Get Macro definitions and write to cmake file.

        """

        tree = data['vcxproj']['tree']
        ns = data['vcxproj']['ns']
        cmake = data['cmake']

        preprocessor = tree.xpath('//ns:PreprocessorDefinitions', namespaces=ns)[0]
        if preprocessor.text:
            cmake.write('# Definition of Macros\n')
            cmake.write('add_definitions(\n')
            for preproc in preprocessor.text.split(";"):
                if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                    cmake.write('   -D%s \n' % preproc)
            # Unicode
            u = tree.find("//ns:CharacterSet", namespaces=ns)
            if 'Unicode' in u.text:
                cmake.write('   -DUNICODE\n')
                cmake.write('   -D_UNICODE\n')
            cmake.write(')\n\n')
