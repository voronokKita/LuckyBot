""" python tests/testsuite.py """
import sys

if __name__ != '__main__':
    print('Run testsuite.py as main.')
    sys.exit(1)

import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from tests import test_base
from tests.integration import test_main


test_modules = [test_base]

suite_list = []
loader = unittest.TestLoader()
for module in test_modules:
    suite = loader.loadTestsFromModule(module)
    suite_list.append(suite)

big_suite_of_units = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(big_suite_of_units)

unittest.TextTestRunner(verbosity=2).run(
    loader.loadTestsFromModule(test_main)
)
