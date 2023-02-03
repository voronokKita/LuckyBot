""" python -m unittest tests.integration.controller.test_controller_with_imq """
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.constants import TestException, IMQException, PROJECT_DIR
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.receiver import InputQueue
from lucky_bot.controller.controller import Controller
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadSmallTestTemplate


@patch('lucky_bot.controller.controller.ControllerThread._test_controller_cycle')
@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.Controller.responder')
class TestControllerWithMessageQueue(ThreadSmallTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        InputQueue.set_up()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        InputQueue.tear_down()

    @patch('lucky_bot.controller.controller.Controller._process_the_message')
    def test_controller_with_imq_integration(self, process_the_message, *args):
        InputQueue.add_message('foo', time=1)
        InputQueue.add_message('bar', time=2)
        InputQueue.add_message('baz', time=3)

        Controller.check_new_messages()

        self.assertEqual(process_the_message.call_count, 3)
        self.assertIsNone(InputQueue.get_first_message())

    def test_controller_normal_messages(self, respond, bot, controller_cycle):
        InputQueue.add_message('/sender delete 42', time=1)
        InputQueue.add_message(self.telegram_request, time=2)
        INCOMING_MESSAGE.set()

        self.thread_obj.start()
        if not CONTROLLER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the controller has passed.')

        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        respond.delete_user.assert_called_once_with('42')
        bot.process_new_updates.assert_called_once()
        self.assertIsNone(InputQueue.get_first_message(), msg='first')
        controller_cycle.assert_not_called()

        InputQueue.add_message('/sender delete 404', time=3)
        INCOMING_MESSAGE.set()
        sleep(0.2)
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(respond.delete_user.call_count, 2, msg='cycle')
        bot.process_new_updates.assert_called_once()
        self.assertIsNone(InputQueue.get_first_message(), msg='cycle')
        controller_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.thread_obj.merge()
        controller_cycle.assert_called_once()

    @patch('lucky_bot.receiver.input_mq.test_func2')
    def test_controller_imq_exception(self, func, *args):
        func.side_effect = TestException('boom')

        self.thread_obj.start()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.assertRaises(IMQException, self.thread_obj.merge)
