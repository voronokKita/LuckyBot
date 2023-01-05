""" python -m unittest tests.units.test_sender """
import unittest
from unittest.mock import patch, Mock

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import (
    TestException, DispatcherTimeout,
    DispatcherUndefinedExc, DispatcherException,
    StopTheSenderGently, DispatcherWrongToken, DispatcherNoAccess,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    EXIT_SIGNAL, NEW_MESSAGE_TO_SEND,
)
from lucky_bot.models.output_mq import OutputQueue
from lucky_bot import dispatcher
from lucky_bot.sender import SenderThread

from tests.presets import ThreadTestTemplate


@patch('lucky_bot.sender.SenderThread._process_all_messages')
class TestSenderThreadBase(ThreadTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def test_sender_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.sender.SenderThread._test_exception_after_signal')
    def test_sender_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)


@patch('lucky_bot.sender.SenderThread._test_sender_cycle')
@patch('lucky_bot.sender.dispatcher')
@patch('lucky_bot.sender.OutputQueue')
class TestSender(unittest.TestCase):
    def setUp(self):
        self.sender = SenderThread()

    def tearDown(self):
        if self.sender.is_alive():
            self.sender.merge()
        self._clear_signals()

    @staticmethod
    def _clear_signals():
        signals = [EXIT_SIGNAL, NEW_MESSAGE_TO_SEND,
                   SENDER_IS_RUNNING, SENDER_IS_STOPPED]
        [signal.clear() for signal in signals if signal.is_set()]

    def test_sender_normal_message(self, mock_OutputQueue, disp, sender_cycle):
        msg_obj = Mock()
        msg_obj.destination = 42
        msg_obj.text = 'hello'
        mock_OutputQueue.get_first_message.side_effect = [msg_obj, None]
        disp.send_message.return_value = True

        self.sender.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.sender.merge()
            raise TestException('The time to start the sender has passed.')

        self.assertFalse(EXIT_SIGNAL.is_set())
        disp.send_message.assert_called_once_with(42, 'hello')
        mock_OutputQueue.delete_message.assert_called_once_with(msg_obj)

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.sender.merge()
            raise TestException('The time to stop the sender has passed.')

        sender_cycle.assert_not_called()
        self.sender.merge()
        self.assertFalse(self.sender.is_alive())

    @patch('lucky_bot.sender.SenderThread._process_a_delivery')
    def test_sender_exception_stop_gently(self, func, mock_OutputQueue, disp, sender_cycle):
        mock_OutputQueue.get_first_message.side_effect = [Mock(), None]
        func.side_effect = StopTheSenderGently('please')

        self.sender.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.sender.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(self.sender.is_alive())
        self.sender.merge()  # no exceptions

    def test_sender_exception_in_dispatcher(self, mock_OutputQueue, disp, sender_cycle):
        mock_OutputQueue.get_first_message.side_effect = [Mock(), None]
        disp.send_message.side_effect = DispatcherException('boom')

        self.sender.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.sender.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(self.sender.is_alive())
        self.assertRaises(DispatcherException, self.sender.merge)


@patch('lucky_bot.sender.OutputQueue')
@patch('lucky_bot.sender.dispatcher')
class TestSenderCallToDispatcher(unittest.TestCase):
    ''' The dispatcher exceptions that are caught in sender after a call. '''

    def test_sender_call_exception_wrong_token(self, disp, queue):
        disp.send_message.side_effect = DispatcherWrongToken('boom')
        self.assertRaises(StopTheSenderGently, SenderThread._process_a_delivery, Mock())
        queue.delete_message.assert_not_called()

    def test_sender_call_exception_timeout(self, disp, queue):
        disp.send_message.side_effect = DispatcherTimeout('boom')
        self.assertRaises(StopTheSenderGently, SenderThread._process_a_delivery, Mock())
        queue.delete_message.assert_not_called()

    def test_sender_call_exception_undefined(self, disp, queue):
        disp.send_message.side_effect = DispatcherUndefinedExc('boom')
        SenderThread._process_a_delivery(Mock())
        queue.delete_message.assert_called_once()

    def test_sender_call_exception_access(self, disp, queue):
        disp.send_message.side_effect = DispatcherNoAccess('boom')
        SenderThread._process_a_delivery(Mock())
        queue.delete_message.assert_called_once()
        # TODO delete a uid request

    def test_sender_call_exception_in_dispatcher(self, disp, queue):
        disp.send_message.side_effect = DispatcherException('boom')
        self.assertRaises(DispatcherException, SenderThread._process_a_delivery, Mock())
        queue.delete_message.assert_not_called()

    def test_sender_call_exception_normal(self, disp, queue):
        disp.send_message.side_effect = Exception('boom')
        self.assertRaises(DispatcherException, SenderThread._process_a_delivery, Mock())
        queue.delete_message.assert_not_called()

    def test_sender_call_dispatcher_normal(self, disp, queue):
        msg_obj = Mock()
        msg_obj.destination = 42
        msg_obj.text = 'hello'

        SenderThread._process_a_delivery(msg_obj)
        disp.send_message.assert_called_once_with(42, 'hello')
        queue.delete_message.assert_called_once_with(msg_obj)


class TestSenderMessageQueue(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()

    def tearDown(self):
        OutputQueue.tear_down()

    def test_output_queue_works(self):
        OutputQueue.add_message(42, 'foo', 1)
        OutputQueue.add_message(42, 'bar', 2)
        OutputQueue.add_message(42, 'baz', 3)

        for message in ['foo', 'bar', 'baz']:
            msg_obj = OutputQueue.get_first_message()
            self.assertIsNotNone(msg_obj, msg=message)
            self.assertEqual(msg_obj.text, message)
            OutputQueue.delete_message(msg_obj)

        result = OutputQueue.get_first_message()
        self.assertIsNone(result)


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
