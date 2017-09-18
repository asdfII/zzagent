# -*- coding: utf-8 -*-

import os
import sys
import platform

try:
    param = sys.argv[1]
except IndexError:
    param = 'pyc'


def del_pyc_or_suffix(param='pyc'):
    if platform.system() == 'Windows':
        os.system('del /q /f /s *.' + param)
    if platform.system() == 'Linux':
        os.system('rm -fr *.' + param)


del_pyc_or_suffix(param)
