""" python -m unittest tests.units.test_sender """
import unittest
from unittest.mock import patch, Mock

from telebot.apihelper import ApiTelegramException

from lucky_bot.sender import SenderThread
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED, EXIT_SIGNAL,
    NEW_MESSAGE_TO_SEND,
)
from lucky_bot.helpers.constants import (
    TestException,
    DispatcherTimeout, DispatcherUndefinedExc, DispatcherException,
    StopTheSenderGently, DispatcherWrongToken, DispatcherNoAccess,
)
from lucky_bot.models.output_mq import OutputQueue
from lucky_bot import dispatcher

from tests.presets import ThreadTestTemplate


class TestSenderBase(ThreadTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    @patch('lucky_bot.sender.SenderThread._process_all_messages')
    def test_sender_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.sender.SenderThread._process_all_messages')
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_sender_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    @patch('lucky_bot.sender.SenderThread._test_sender_cycle')
    @patch('lucky_bot.sender.send_message')
    @patch('lucky_bot.sender.OutputQueue')
    def test_sender_normal_message(self, mock_OutputQueue, send_message, sender_cycle):
        msg_obj = Mock()
        msg_obj.destination = 42
        msg_obj.text = 'hello'
        mock_OutputQueue.get_first_message.side_effect = [msg_obj, None]
        send_message.return_value = True

        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        self.assertFalse(EXIT_SIGNAL.is_set())
        send_message.assert_called_once_with(42, 'hello')
        mock_OutputQueue.delete_message.assert_called_once_with(msg_obj)

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        sender_cycle.assert_not_called()
        self.thread_obj.merge()

    def sender_exception_after_message_signal(self, *args):
        pass


class SenderMessageQueue(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()

    def tearDown(self):
        OutputQueue.tear_down()

    def test_output_queue_works(self):
        OutputQueue.add_message(42, 'foo', 1)
        OutputQueue.add_message(42, 'bar', 2)
        OutputQueue.add_message(42, 'baz', 3)

        msg_obj = OutputQueue.get_first_message()
        self.assertIsNotNone(msg_obj, msg='foo')
        self.assertEqual(msg_obj.text, 'foo')
        OutputQueue.delete_message(msg_obj)

        msg_obj = OutputQueue.get_first_message()
        self.assertIsNotNone(msg_obj, msg='bar')
        self.assertEqual(msg_obj.text, 'bar')
        OutputQueue.delete_message(msg_obj)

        msg_obj = OutputQueue.get_first_message()
        self.assertIsNotNone(msg_obj, msg='baz')
        self.assertEqual(msg_obj.text, 'baz')
        OutputQueue.delete_message(msg_obj)

        result = OutputQueue.get_first_message()
        self.assertIsNone(result)

    def from_queue_to_sender(self):
        pass


@patch('lucky_bot.dispatcher.time')
@patch('lucky_bot.dispatcher.BOT')
class TestDispatcher(unittest.TestCase):
    def test_dispatcher_normal_case(self, bot, *args):
        dispatcher.send_message(42, 'hello')
        bot.send_message.assert_called_once_with(42, 'hello')

    def test_dispatcher_normal_exception(self, bot, *args):
        bot.send_message.side_effect = TestException('boom')
        self.assertRaises(DispatcherException, dispatcher.send_message, 42, 'hello')

    def test_dispatcher_undefined_exception(self, bot, time):
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 409, 'description': 'undefined telegram problem'}
        )
        bot.send_message.side_effect = exc
        self.assertRaises(DispatcherUndefinedExc, dispatcher.send_message, 42, 'hello')
        self.assertEqual(time.sleep.call_count, 2)

    def test_dispatcher_timeout_exception(self, bot, time):
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 429, 'description': 'Too many requests'}
        )
        bot.send_message.side_effect = exc
        self.assertRaises(DispatcherTimeout, dispatcher.send_message, 42, 'hello')
        self.assertEqual(time.sleep.call_count, 2)

    def test_dispatcher_blocked_exception(self, bot, *args):
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 403, 'description': 'Forbidden: bot blocked by user'}
        )
        bot.send_message.side_effect = exc
        self.assertRaises(DispatcherNoAccess, dispatcher.send_message, 42, 'hello')

    def test_dispatcher_not_found_exception(self, bot, *args):
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 400, 'description': 'Bad request: user not found'}
        )
        bot.send_message.side_effect = exc
        self.assertRaises(DispatcherNoAccess, dispatcher.send_message, 42, 'hello')

    def test_dispatcher_token_exception(self, bot, *args):
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 401, 'description': 'Unauthorized'}
        )
        bot.send_message.side_effect = exc
        self.assertRaises(DispatcherWrongToken, dispatcher.send_message, 42, 'hello')
