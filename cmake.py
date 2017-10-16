from message import send


class CMake(object):
    """
    CMake : create and open CMakeLists.txt

    """

    def __init__(self):
        self.cmake = None

    def create_cmake(self, cmake_path=None):
        """
        Create CMakeLists.txt file in wanted path

        :param cmake_path: path where CMakeLists.txt should be write
        :type cmake_path: str
        """

        if cmake_path is None:
            send('CMakeLists will be build in current directory.', '')
            self.cmake = open('CMakeLists.txt', 'w')
        else:
            send('CmakeLists.txt will be build in : ' + str(cmake_path), 'warn')
            if cmake_path[-1:] == '/' or cmake_path[-1:] == '\\':
                self.cmake = open(str(cmake_path) + 'CMakeLists.txt', 'w')
            else:
                self.cmake = open(str(cmake_path) + '/CMakeLists.txt', 'w')
