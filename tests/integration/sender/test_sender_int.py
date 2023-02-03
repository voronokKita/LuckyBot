""" python -m unittest tests.integration.sender.test_sender_int """
import time
from unittest.mock import patch

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import (
    TestException, SenderException,
    OutputDispatcherException, OMQException,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    EXIT_SIGNAL, NEW_MESSAGE_TO_SEND
)
from lucky_bot.sender import OutputQueue
from lucky_bot.sender import SenderThread

from tests.presets import ThreadSmallTestTemplate


@patch('lucky_bot.sender.sender.SenderThread._test_sender_cycle')
@patch('lucky_bot.sender.output_dispatcher.BOT')
class TestSenderWorks(ThreadSmallTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def setUp(self):
        OutputQueue.set_up()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        OutputQueue.tear_down()

    def test_sender_integration_normal_case(self, disp_bot, sender_cycle):
        uid1 = '42'
        text1 = 'hello'
        OutputQueue.add_message(uid1, text1)

        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        disp_bot.send_message.assert_called_once_with(uid1, text1)
        sender_cycle.assert_not_called()
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='first msg')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first msg')

        uid2 = '142'
        text2 = 'world'
        OutputQueue.add_message(uid2, text2)
        NEW_MESSAGE_TO_SEND.set()
        time.sleep(0.4)

        sender_cycle.assert_called_once()
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(disp_bot.send_message.call_count, 2)
        disp_bot.send_message.assert_called_with(uid2, text2)

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.thread_obj.merge()

    def test_sender_forced_merge(self, *args):
        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        self.thread_obj.merge()
        self.assertTrue(EXIT_SIGNAL.is_set())

    def test_sender_cycle_exception(self, arg1, sender_cycle):
        sender_cycle.side_effect = TestException('boom')

        self.thread_obj.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertRaises(SenderException, self.thread_obj.merge)

    @patch('lucky_bot.sender.output_mq.test_func')
    def test_sender_exception_in_omq(self, func, *args):
        func.side_effect = TestException('boom')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertRaises(OMQException, self.thread_obj.merge)

    def test_sender_stops_gently(self, disp_bot, *args):
        OutputQueue.add_message(3, 'foo')
        exc = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 401, 'description': 'Unauthorized'}
        )
        disp_bot.send_message.side_effect = exc

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set())
        self.assertFalse(SENDER_IS_RUNNING.is_set())
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.thread_obj.merge()  # no exceptions

    def test_sender_dispatcher_exception(self, disp_bot, sender_cycle):
        OutputQueue.add_message(4, 'bar')
        disp_bot.send_message.side_effect = TestException('boom')

        self.thread_obj.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the sender has passed.')

        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set())
        self.assertFalse(SENDER_IS_RUNNING.is_set())
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(OutputDispatcherException, self.thread_obj.merge)
