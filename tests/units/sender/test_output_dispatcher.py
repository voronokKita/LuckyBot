""" python -m unittest tests.units.sender.test_output_dispatcher """
import unittest
from unittest.mock import patch

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import (
    TestException, DispatcherTimeout,
    DispatcherUndefinedExc, OutputDispatcherException,
    DispatcherWrongToken, DispatcherNoAccess,
)
from lucky_bot.sender import output_dispatcher as dispatcher


@patch('lucky_bot.sender.output_dispatcher.time')
@patch('lucky_bot.sender.output_dispatcher.BOT')
class TestOutputDispatcher(unittest.TestCase):
    def test_dispatcher_normal_case(self, bot, *args):
        dispatcher.send_message(42, 'hello')
        bot.send_message.assert_called_once_with(42, 'hello')

    def test_dispatcher_normal_exception(self, bot, *args):
        bot.send_message.side_effect = TestException('boom')
        self.assertRaises(OutputDispatcherException, dispatcher.send_message, 42, 'hello')

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
