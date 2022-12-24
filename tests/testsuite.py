""" python tests/testsuite.py """

import sys
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from tests import test_base


def execute():
    test_modules = [test_base]

    suite_list = []
    loader = unittest.TestLoader()
    for module in test_modules:
        suite = loader.loadTestsFromModule(module)
        suite_list.append(suite)
    big_suite = unittest.TestSuite(suite_list)

    unittest.TextTestRunner(verbosity=2).run(big_suite)


if __name__ == '__main__':
    execute()
