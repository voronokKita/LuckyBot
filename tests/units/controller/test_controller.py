""" python -m unittest tests.units.controller.test_controller """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.constants import (
    TestException, TelebotHandlerException, PROJECT_DIR,
)
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.controller.controller import Controller
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


@patch('lucky_bot.controller.controller.Controller.check_new_messages')
class TestControllerThreadBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    signal_after_exit = INCOMING_MESSAGE

    def test_controller_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_controller_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_controller_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.Controller.responder')
class TestControllerCallToResponder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        self.controller = Controller()

    def test_internal_sender_delete(self, respond, *args):
        msg_data = '/sender delete 42'
        self.controller._process_the_message(msg_data)
        respond.delete_user.assert_called_once_with('42')

    def test_telegram_message(self, arg, bot):
        msg_data = self.telegram_request
        self.controller._process_the_message(msg_data)
        bot.process_new_updates.assert_called_once()

    def test_telegram_message_exception(self, arg, bot):
        msg_data = self.telegram_request
        bot.process_new_updates.side_effect = TestException('boom')

        self.assertRaises(TelebotHandlerException,
                          self.controller._process_the_message,
                          msg_data)


@patch('lucky_bot.controller.controller.ControllerThread._test_controller_cycle')
@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.Controller.responder')
@patch('lucky_bot.controller.controller.InputQueue')
class TestSenderExecution(ThreadSmallTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def test_sender_normal_message(self, imq, responder, bot, controller_cycle):
        msg_obj1 = (1, '/sender delete 42')
        msg_obj2 = (2, self.telegram_request)
        imq.get_first_message.side_effect = [msg_obj1, msg_obj2, None]
        INCOMING_MESSAGE.set()

        self.thread_obj.start()
        if not CONTROLLER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the controller has passed.')

        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        responder.delete_user.assert_called_once_with('42')
        bot.process_new_updates.assert_called_once()
        self.assertEqual(imq.delete_message.call_count, 2, msg='first')
        controller_cycle.assert_not_called()

        msg_obj3 = (3, '/sender delete 404')
        imq.get_first_message.side_effect = [msg_obj3, None]
        INCOMING_MESSAGE.set()
        sleep(0.2)
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(responder.delete_user.call_count, 2, msg='cycle')
        bot.process_new_updates.assert_called_once()
        self.assertEqual(imq.delete_message.call_count, 3, msg='cycle')
        controller_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.thread_obj.merge()
        controller_cycle.assert_called_once()

    def test_controller_exception_in_message_process(self, imq, responder, bot, controller_cycle):
        msg_obj = (1, self.telegram_request)
        imq.get_first_message.side_effect = [msg_obj, None]
        bot.process_new_updates.side_effect = TestException('boom')

        self.thread_obj.start()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.assertFalse(CONTROLLER_IS_RUNNING.is_set(), msg='exception before this signal')
        controller_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(TelebotHandlerException, self.thread_obj.merge)
