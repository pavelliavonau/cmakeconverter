# -*- coding: utf-8 -*-

import os

def send(message, status):
    """
    send message during execution of script
    :param message: content of message
    :param status: level of message
    :return:
    """
    FAIL = ''
    WARN = ''
    OK = ''
    ENDC = ''

    if os.name == 'posix':
        FAIL += '\033[91m'
        OK += '\033[34m'
        ENDC += '\033[0m'
        WARN += '\033[93m'
    if status == 'error':
        print('ERR  : ' + FAIL + message + ENDC)
    elif status == 'warn':
        print('WARN : ' + WARN + message + ENDC)
    elif status == 'ok':
        print('OK   : ' + OK + message + ENDC)
    else:
        print('INFO : ' + message)