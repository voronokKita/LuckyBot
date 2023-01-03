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
from tests.units import (
    test_webhook, test_input_controller, test_updater,
    test_sender,
)
from tests.integration import test_main, test_webhook_int


loader = unittest.TestLoader()

result = unittest.TextTestRunner(verbosity=2).run(
    loader.loadTestsFromModule(test_base)
)
if result.wasSuccessful() is False:
    sys.exit(1)

modules_to_test = {
    test_sender,
    test_updater,
    test_input_controller,
    test_webhook,
    test_main,
    test_webhook_int,
}
suite_list = []
for module in modules_to_test:
    suite = loader.loadTestsFromModule(module)
    suite_list.append(suite)
big_suite_of_tests = unittest.TestSuite(suite_list)

unittest.TextTestRunner(verbosity=2).run(big_suite_of_tests)
