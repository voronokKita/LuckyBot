""" python -m unittest tests.integration.controller.test_controller_int """
from time import sleep
from unittest.mock import patch

from lucky_bot.helpers.constants import TestException, PROJECT_DIR
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, NEW_MESSAGE_TO_SEND, EXIT_SIGNAL,
)
from lucky_bot import MainDB
from lucky_bot.receiver import InputQueue
from lucky_bot.sender import OutputQueue
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadSmallTestTemplate


@patch('lucky_bot.controller.controller.ControllerThread._test_controller_cycle')
class TestControllerWorks(ThreadSmallTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE, NEW_MESSAGE_TO_SEND]

    @classmethod
    def setUpClass(cls):
        cls.uid = 1266575762
        cls.username = 'john_doe'
        fixtures = PROJECT_DIR / 'tests' / 'fixtures'
        with open(fixtures / 'telegram_request.json') as f:
            cls.telegram_text = f.read().strip()
        with open(fixtures / 'telegram_start.json') as f:
            cls.telegram_start = f.read().strip()

    def setUp(self):
        MainDB.set_up()
        InputQueue.set_up()
        OutputQueue.set_up()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        OutputQueue.tear_down()
        InputQueue.tear_down()
        MainDB.tear_down()

    def test_controller_cmd_start(self, controller_cycle):
        InputQueue.add_message(self.telegram_start, 1)
        INCOMING_MESSAGE.set()

        self.thread_obj.start()
        if not NEW_MESSAGE_TO_SEND.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to put the 1st message in the OMQ has passed.')

        if not CONTROLLER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the controller has passed.')

        sleep(0.2)
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='first')
        self.assertIsNone(InputQueue.get_first_message(), msg='first')
        controller_cycle.assert_not_called()

        msg1 = OutputQueue.get_first_message()
        self.assertIsNotNone(msg1)
        user = MainDB.get_user(self.uid)
        self.assertIsNotNone(user)

        OutputQueue.delete_message(msg1)
        NEW_MESSAGE_TO_SEND.clear()

        # 2nd msg
        InputQueue.add_message(self.telegram_text, 2)
        INCOMING_MESSAGE.set()
        if not NEW_MESSAGE_TO_SEND.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to put the 2nd message in the OMQ has passed.')

        sleep(0.2)
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='cycle')
        self.assertIsNone(InputQueue.get_first_message(), msg='cycle')
        controller_cycle.assert_called_once()

        msg2 = OutputQueue.get_first_message()
        self.assertIsNotNone(msg2)

        EXIT_SIGNAL.set()
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.thread_obj.merge()
        controller_cycle.assert_called_once()
