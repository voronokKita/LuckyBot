""" python -m unittest tests.integration.test_sender_int """
import time
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


# TODO NEW_MESSAGE_TO_SEND cycle in normal tests


@patch('lucky_bot.sender.SenderThread._test_sender_cycle')
@patch('lucky_bot.dispatcher.BOT')
class TestSenderWorks(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()
        self.sender = SenderThread()

    def tearDown(self):
        if self.sender.is_alive():
            self.sender.merge()
        self._clear_signals()
        OutputQueue.tear_down()

    @staticmethod
    def _clear_signals():
        signals = [EXIT_SIGNAL, NEW_MESSAGE_TO_SEND,
                   SENDER_IS_RUNNING, SENDER_IS_STOPPED]
        [signal.clear() for signal in signals if signal.is_set()]

    def test_sender_integration_normal_case(self, disp_bot, sender_cycle):
        OutputQueue.add_message(42, 'hello', 1)

        self.sender.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.sender.merge()
            raise TestException('The time to start the sender has passed.')

        disp_bot.send_message.assert_called_once_with(42, 'hello')
        sender_cycle.assert_not_called()
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='first msg')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first msg')

        OutputQueue.add_message(42, 'world', 2)
        NEW_MESSAGE_TO_SEND.set()
        time.sleep(0.1)

        sender_cycle.assert_called_once()
        self.assertFalse(NEW_MESSAGE_TO_SEND.is_set(), msg='second msg')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='second msg')
        self.assertEqual(disp_bot.send_message.call_count, 2)
        disp_bot.send_message.assert_called_with(42, 'world')

        EXIT_SIGNAL.set()
        NEW_MESSAGE_TO_SEND.set()
        if not SENDER_IS_STOPPED.wait(10):
            self.sender.merge()
            raise TestException('The time to stop the sender has passed.')

        self.sender.merge()




