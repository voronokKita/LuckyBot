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
from tests.units import test_database
from tests.units.updater import test_updater
from tests.units.sender import test_omq
from tests.units.sender import test_dispatcher
from tests.units.sender import test_sender
from tests.units.receiver import test_imq
from tests.units.receiver import test_flask_app
from tests.units.receiver import test_receiver
from tests.units.controller import test_bot_handlers
from tests.units.controller import test_responder
from tests.units.controller import test_controller

from tests.integration.sender import test_sender_int
from tests.integration.receiver import test_receiver_int, test_flask_with_imq
from tests.integration.controller import test_controller_int
from tests.integration import test_main

loader = unittest.TestLoader()

result = unittest.TextTestRunner(verbosity=2).run(
    loader.loadTestsFromModule(test_base)
)
if result.wasSuccessful() is False:
    # don't go farther if the base tests are failed
    sys.exit(1)

modules_to_test = {
    test_database,

    test_updater,

    test_omq,
    test_dispatcher,
    test_sender,

    test_imq,
    test_flask_app,
    test_receiver,

    test_bot_handlers,
    test_responder,
    test_controller,

    test_sender_int,
    test_flask_with_imq,
    test_receiver_int,
    test_controller_int,
    test_main,
}
suite_list = []
for module in modules_to_test:
    suite = loader.loadTestsFromModule(module)
    suite_list.append(suite)
big_suite_of_tests = unittest.TestSuite(suite_list)

unittest.TextTestRunner(verbosity=2).run(big_suite_of_tests)
