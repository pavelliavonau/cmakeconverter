# -*- coding: utf-8 -*-

from lxml import etree

import message as msg

class Vcxproj(object):
    """
    This class prepare data for parsing. Retrieve root xml and namespace.
    """

    def __init__(self):
        self.vcxproj = ''

    def create_data(self, vcxproj=''):
        """
        Get xml data from vcxproj
        """

        try:
            tree = etree.parse(vcxproj)
            namespace = str(tree.getroot().nsmap)
            ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}

            self.vcxproj = {
                'tree': tree,
                'ns': ns
            }
        except OSError:
            msg.send('.vcxproj file can not be import. Please, verify you have rights to access this directory !', 'error')
        except etree.XMLSyntaxError:
            msg.send('This file is not a file.vcxproj or xml is broken !', 'error')

    def get_data(self):
        return self.vcxproj