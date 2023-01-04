""" python -m unittest tests.units.test_sender """
import unittest
from unittest.mock import patch

from lucky_bot.sender import SenderThread
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED, EXIT_SIGNAL,
)
from lucky_bot.models.output_mq import OutputQueue

from tests.presets import ThreadTestTemplate


class TestSenderBase(ThreadTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def test_sender_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_sender_exception_case(self, test_exception):
        super().exception_case(test_exception)

    def sender_exception_after_message_signal(self):
        pass

    def sender_message(self):
        pass


class SenderMessageQueue(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()

    def tearDown(self):
        OutputQueue.tear_down()

    def test_output_queue_works(self):
        OutputQueue.add_message('foo', 1)
        OutputQueue.add_message('bar', 2)
        OutputQueue.add_message('baz', 3)

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
