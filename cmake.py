
import message as msg

class CMake(object):

    def __init__(self):
        self.cmake = None

    def create_cmake(self, cmake_path=None):
        if cmake_path is None:
            msg.send('CMakeLists will be build in current directory.', 'ok')
        else:
            msg.send('CmakeLists.txt will be build in : ' + str(cmake_path), 'warn')

        self.cmake = str(cmake_path) + 'CMakeLists.txt'
        print('IN cmake.py = ' + str(self.cmake))

    def get_cmake(self):
        return self.cmake