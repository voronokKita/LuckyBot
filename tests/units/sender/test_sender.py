""" python -m unittest tests.units.sender.test_sender """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.constants import (
    TestException, DispatcherTimeout, IMQException,
    DispatcherUndefinedExc, OutputDispatcherException,
    StopTheSenderGently, DispatcherWrongToken, DispatcherNoAccess,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    EXIT_SIGNAL, NEW_MESSAGE_TO_SEND, INCOMING_MESSAGE,
)
from lucky_bot.sender.sender import Sender
from lucky_bot.sender import SenderThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


@patch('lucky_bot.sender.sender.Sender.process_outgoing_messages')
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
@patch('lucky_bot.sender.sender.output_dispatcher')
@patch('lucky_bot.sender.sender.OutputQueue')
@patch('lucky_bot.sender.sender.InputQueue')
class TestSenderExecution(ThreadSmallTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED
    other_signals = [NEW_MESSAGE_TO_SEND, INCOMING_MESSAGE]

    def test_sender_normal_message(self, imq, omq, disp, sender_cycle):
        id_ = 1
        uid = '42'
        text = 'hello'
        message = (id_, uid, text)
        omq.get_first_message.side_effect = [message, None]
        NEW_MESSAGE_TO_SEND.set()

        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='first msg')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first msg')
        disp.send_message.assert_called_once_with(uid, text)
        omq.delete_message.assert_called_once_with(id_)
        imq.assert_not_called()
        sender_cycle.assert_not_called()

        omq.get_first_message.side_effect = [message, None]
        NEW_MESSAGE_TO_SEND.set()
        sleep(0.2)
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(disp.send_message.call_count, 2, msg='cycle')
        self.assertEqual(omq.delete_message.call_count, 2, msg='cycle')
        imq.assert_not_called()
        sender_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.thread_obj.merge()
        sender_cycle.assert_called_once()

    @patch('lucky_bot.sender.sender.Sender._handle_a_delivery')
    def test_sender_exception_stop_gently(self, func, imq, omq, disp, sender_cycle):
        omq.get_first_message.side_effect = [(1, '9', 'foobar'), None]
        func.side_effect = StopTheSenderGently('pretty please')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.thread_obj.merge()  # no exceptions, just stops

    def test_sender_exception_in_dispatcher(self, imq, omq, disp, sender_cycle):
        omq.get_first_message.side_effect = [(2, '33', 'bazqux'), None]
        disp.send_message.side_effect = OutputDispatcherException('boom')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(SENDER_IS_RUNNING.is_set(), msg='exception before this signal')
        sender_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(OutputDispatcherException, self.thread_obj.merge)


@patch('lucky_bot.sender.sender.InputQueue')
@patch('lucky_bot.sender.sender.output_dispatcher')
class TestSenderCallToDispatcher(unittest.TestCase):
    ''' The dispatcher exceptions that are caught in sender after a call. '''

    def test_sender_call_exception_wrong_token(self, disp, imq):
        disp.send_message.side_effect = DispatcherWrongToken('boom')
        self.assertRaises(StopTheSenderGently, Sender._handle_a_delivery, 1, 'foo')

    def test_sender_call_exception_timeout(self, disp, imq):
        disp.send_message.side_effect = DispatcherTimeout('boom')
        self.assertRaises(StopTheSenderGently, Sender._handle_a_delivery, 2, 'bar')

    def test_sender_call_exception_undefined(self, disp, imq):
        disp.send_message.side_effect = DispatcherUndefinedExc('boom')
        Sender._handle_a_delivery(3, 'baz')

    def test_sender_call_exception_no_access(self, disp, imq):
        disp.send_message.side_effect = DispatcherNoAccess('boom')
        Sender._handle_a_delivery(4, 'qux')

        imq.add_message.assert_called_once()
        self.assertTrue(INCOMING_MESSAGE.is_set())
        INCOMING_MESSAGE.clear()

    def test_sender_call_dispatcher_imq_exception(self, disp, imq):
        disp.send_message.side_effect = DispatcherNoAccess('boom')
        imq.add_message.side_effect = IMQException('badoom')

        self.assertRaises(IMQException, Sender._handle_a_delivery, 5, 'quux')
        self.assertFalse(INCOMING_MESSAGE.is_set())

    def test_sender_call_exception_in_dispatcher(self, disp, imq):
        disp.send_message.side_effect = OutputDispatcherException('boom')
        self.assertRaises(OutputDispatcherException, Sender._handle_a_delivery, 6, 'corge')

    def test_sender_call_exception_normal(self, disp, imq):
        disp.send_message.side_effect = Exception('boom')
        self.assertRaises(OutputDispatcherException, Sender._handle_a_delivery, 7, 'grault')

    def test_sender_call_dispatcher_normal(self, disp, imq):
        Sender._handle_a_delivery(8, 'garply')
        disp.send_message.assert_called_once_with(8, 'garply')
