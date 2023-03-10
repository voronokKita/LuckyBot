""" python tests/testkit.py """
import sys

if __name__ != '__main__':
    print('Run testkit.py as main.')
    sys.exit(1)

import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from tests import test_base
from tests.units import test_database
from tests.units.updater import test_update_dispatcher
from tests.units.updater import test_updater
from tests.units.sender import test_omq
from tests.units.sender import test_output_dispatcher
from tests.units.sender import test_sender
from tests.units.receiver import test_imq
from tests.units.receiver import test_flask_app
from tests.units.receiver import test_receiver
from tests.units.controller import test_bot_handlers
from tests.units.controller import test_responder
from tests.units.controller import test_controller

from tests.integration.updater import test_updater_int
from tests.integration.sender import test_sender_int
from tests.integration.receiver import test_receiver_int, test_flask_with_imq
from tests.integration.controller import test_controller_int
from tests.integration.controller import test_controller_with_imq
from tests.integration.controller import test_parser_with_db
from tests.integration.controller import test_responder_integration
from tests.integration import test_sender_receiver_controller
from tests.integration import test_main

loader = unittest.TestLoader()
test_runner = unittest.TextTestRunner(verbosity=2)


base_result = test_runner.run(loader.loadTestsFromModule(test_base))
if base_result.wasSuccessful() is False:
    # don't go farther if the base tests are failed
    sys.exit(1)


print('\n------------------------------unit tests------------------------------')
unit_tests = {
    test_database,

    test_update_dispatcher,
    test_updater,

    test_omq,
    test_output_dispatcher,
    test_sender,

    test_imq,
    test_flask_app,
    test_receiver,

    test_bot_handlers,
    test_responder,
    test_controller,
}
unit_list = []
for module in unit_tests:
    suite = loader.loadTestsFromModule(module)
    unit_list.append(suite)
big_suite_of_unit_tests = unittest.TestSuite(unit_list)

units_result = test_runner.run(big_suite_of_unit_tests)
if units_result.wasSuccessful() is False:
    sys.exit(2)


print('\n--------------------------integration tests---------------------------')
integration_tests = {
    test_updater_int,

    test_sender_int,

    test_flask_with_imq,
    test_receiver_int,

    test_parser_with_db,
    test_responder_integration,
    test_controller_with_imq,
    test_controller_int,

    test_sender_receiver_controller,
    test_main,
}
int_list = []
for module in integration_tests:
    suite = loader.loadTestsFromModule(module)
    int_list.append(suite)
big_suite_of_integration_tests = unittest.TestSuite(int_list)

test_runner.run(big_suite_of_integration_tests)
