""" python -m unittest tests.units.sender.test_sender """
import unittest
from unittest.mock import patch, Mock
from time import sleep

from lucky_bot.helpers.constants import (
    TestException, DispatcherTimeout,
    DispatcherUndefinedExc, DispatcherException,
    StopTheSenderGently, DispatcherWrongToken, DispatcherNoAccess,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    EXIT_SIGNAL, NEW_MESSAGE_TO_SEND, INCOMING_MESSAGE,
)
from lucky_bot.sender import SenderThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


@patch('lucky_bot.sender.sender.SenderThread._process_all_messages')
class TestSenderThreadBase(ThreadTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def test_sender_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.sender.sender.SenderThread._test_exception_after_signal')
    def test_sender_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_sender_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.sender.sender.SenderThread._test_sender_cycle')
@patch('lucky_bot.sender.sender.dispatcher')
@patch('lucky_bot.sender.sender.OutputQueue')
class TestSender(ThreadSmallTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED
    other_signals = [NEW_MESSAGE_TO_SEND]

    def test_sender_normal_message(self, mock_OutputQueue, disp, sender_cycle):
        msg_obj = Mock()
        msg_obj.destination = 42
        msg_obj.text = 'hello'
        mock_OutputQueue.get_first_message.side_effect = [msg_obj, None]
        NEW_MESSAGE_TO_SEND.set()

        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='first msg')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first msg')
        disp.send_message.assert_called_once_with(42, 'hello')
        mock_OutputQueue.delete_message.assert_called_once_with(msg_obj)
        sender_cycle.assert_not_called()

        mock_OutputQueue.get_first_message.side_effect = [msg_obj, None]
        NEW_MESSAGE_TO_SEND.set()
        sleep(0.2)
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(disp.send_message.call_count, 2, msg='cycle')
        self.assertEqual(mock_OutputQueue.delete_message.call_count, 2, msg='cycle')
        sender_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.thread_obj.merge()
        sender_cycle.assert_called_once()

    @patch('lucky_bot.sender.sender.SenderThread._process_a_delivery')
    def test_sender_exception_stop_gently(self, func, mock_OutputQueue, disp, sender_cycle):
        mock_OutputQueue.get_first_message.side_effect = [Mock(), None]
        func.side_effect = StopTheSenderGently('please')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.thread_obj.merge()  # no exceptions

    def test_sender_exception_in_dispatcher(self, mock_OutputQueue, disp, sender_cycle):
        mock_OutputQueue.get_first_message.side_effect = [Mock(), None]
        disp.send_message.side_effect = DispatcherException('boom')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(DispatcherException, self.thread_obj.merge)


@patch('lucky_bot.sender.sender.InputQueue')
@patch('lucky_bot.sender.sender.dispatcher')
class TestSenderCallToDispatcher(unittest.TestCase):
    ''' The dispatcher exceptions that are caught in sender after a call. '''

    def test_sender_call_exception_wrong_token(self, disp, imq):
        disp.send_message.side_effect = DispatcherWrongToken('boom')
        self.assertRaises(StopTheSenderGently, SenderThread._process_a_delivery, Mock())

    def test_sender_call_exception_timeout(self, disp, imq):
        disp.send_message.side_effect = DispatcherTimeout('boom')
        self.assertRaises(StopTheSenderGently, SenderThread._process_a_delivery, Mock())

    def test_sender_call_exception_undefined(self, disp, imq):
        disp.send_message.side_effect = DispatcherUndefinedExc('boom')
        SenderThread._process_a_delivery(Mock())

    def test_sender_call_exception_access(self, disp, imq):
        disp.send_message.side_effect = DispatcherNoAccess('boom')
        SenderThread._process_a_delivery(Mock())
        imq.add_message.assert_called_once()
        self.assertTrue(INCOMING_MESSAGE.is_set())
        INCOMING_MESSAGE.clear()

    def test_sender_call_exception_in_dispatcher(self, disp, imq):
        disp.send_message.side_effect = DispatcherException('boom')
        self.assertRaises(DispatcherException, SenderThread._process_a_delivery, Mock())

    def test_sender_call_exception_normal(self, disp, imq):
        disp.send_message.side_effect = Exception('boom')
        self.assertRaises(DispatcherException, SenderThread._process_a_delivery, Mock())

    def test_sender_call_dispatcher_normal(self, disp, imq):
        msg_obj = Mock()
        msg_obj.destination = 42
        msg_obj.text = 'hello'

        SenderThread._process_a_delivery(msg_obj)
        disp.send_message.assert_called_once_with(42, 'hello')
