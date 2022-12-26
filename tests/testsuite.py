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
from tests.units import test_webhook
from tests.integration import test_main


loader = unittest.TestLoader()

print('Project base:')
unittest.TextTestRunner(verbosity=2).run(
    loader.loadTestsFromModule(test_base)
)

print('\nUnits:')
test_units = [test_webhook]
suite_list = []
for module in test_units:
    suite = loader.loadTestsFromModule(module)
    suite_list.append(suite)

big_suite_of_units = unittest.TestSuite(suite_list)
unittest.TextTestRunner(verbosity=2).run(big_suite_of_units)

print('\nModules integration:')
unittest.TextTestRunner(verbosity=2).run(
    loader.loadTestsFromModule(test_main)
)
