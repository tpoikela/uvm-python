""" Wrapper for lib2to3 main to use custom fixes folder """

import sys
from lib2to3.main import main

sys.exit(main('fixes'))
