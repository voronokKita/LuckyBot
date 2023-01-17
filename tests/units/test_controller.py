""" python -m unittest tests.units.test_controller """
import unittest
from unittest.mock import patch, Mock
from time import sleep

from lucky_bot.helpers.constants import TestException, ControllerException, PROJECT_DIR
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


@patch('lucky_bot.controller.controller.ControllerThread._check_new_messages')
class TestControllerThreadBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE]

    def test_controller_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_controller_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_controller_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.controller.controller.ControllerThread._test_controller_cycle')
@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.ControllerThread.respond')
@patch('lucky_bot.controller.controller.InputQueue')
class TestSender(ThreadSmallTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE]

    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        super().setUp()
        self.msg_obj1 = Mock()
        self.msg_obj2 = Mock()
        self.msg_obj3 = Mock()

    def test_sender_normal_message(self, mock_InputQueue, respond, bot, controller_cycle):
        self.msg_obj1.data = '/sender delete 42'
        self.msg_obj2.data = self.telegram_request
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj1, self.msg_obj2, None]
        INCOMING_MESSAGE.set()

        self.thread_obj.start()
        if not CONTROLLER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the controller has passed.')

        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        respond.delete_user.assert_called_once_with(42)
        bot.process_new_updates.assert_called_once()
        self.assertEqual(mock_InputQueue.delete_message.call_count, 2, msg='first')
        controller_cycle.assert_not_called()

        self.msg_obj3.data = '/sender delete 404'
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj3, None]
        INCOMING_MESSAGE.set()
        sleep(0.2)
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(respond.delete_user.call_count, 2, msg='cycle')
        bot.process_new_updates.assert_called_once()
        self.assertEqual(mock_InputQueue.delete_message.call_count, 3, msg='cycle')
        controller_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.thread_obj.merge()
        controller_cycle.assert_called_once()

    def test_controller_exception_in_message_process(self, mock_InputQueue, respond, bot, controller_cycle):
        self.msg_obj1.data = self.telegram_request
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj1, None]
        bot.process_new_updates.side_effect = TestException('boom')

        self.thread_obj.start()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.assertFalse(CONTROLLER_IS_RUNNING.is_set(), msg='exception before this signal')
        controller_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(ControllerException, self.thread_obj.merge)


@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.ControllerThread.respond')
class TestControllerCallToResponder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        self.controller = ControllerThread()
        self.msg_obj = Mock()

    def test_internal_sender_delete(self, respond, *args):
        self.msg_obj.data = '/sender delete 42'
        self.controller._process_the_message(self.msg_obj)
        respond.delete_user.assert_called_once_with(42)

    def test_telegram_message(self, arg, bot):
        self.msg_obj.data = self.telegram_request
        self.controller._process_the_message(self.msg_obj)
        bot.process_new_updates.assert_called_once()
