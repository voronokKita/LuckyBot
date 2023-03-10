""" python -m unittest tests.integration.test_sender_receiver_controller """
import unittest
from unittest.mock import patch
from time import sleep

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import TestException, IMQException
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot import MainDB
from lucky_bot.receiver import InputQueue
from lucky_bot.sender import OutputQueue
from lucky_bot.sender import SenderThread
from lucky_bot.controller import ControllerThread

from tests.presets import SIGNALS


@patch('lucky_bot.sender.output_dispatcher.BOT')
class TestSenderReceiverControllerAndDB(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()
        OutputQueue.set_up()
        InputQueue.set_up()
        self.sender = SenderThread()
        self.controller = ControllerThread()

        self.exception = ApiTelegramException(
            function_name='foo', result='bar',
            result_json={'error_code': 403, 'description': 'Forbidden: bot blocked by user'}
        )

    def tearDown(self):
        if self.sender.is_alive():
            self.sender.merge()
        if self.controller.is_alive():
            self.controller.merge()
        InputQueue.tear_down()
        OutputQueue.tear_down()
        MainDB.tear_down()
        [signal.clear() for signal in SIGNALS if signal.is_set()]
        self.assertFalse(self.sender.is_alive())
        self.assertFalse(self.controller.is_alive())

    def test_sender_deletes_user_after_bot_blocked(self, bot):
        bot.send_message.side_effect = self.exception
        user = '42'
        MainDB.add_user(user)
        self.assertIsNotNone(MainDB.get_user(user))
        OutputQueue.add_message(user, 'do something')

        self.sender.start()
        if not SENDER_IS_RUNNING.wait(10):
            self.sender.merge()
            raise TestException('The time to start the sender has passed.')

        self.controller.start()
        if not CONTROLLER_IS_RUNNING.wait(10):
            self.controller.merge()
            raise TestException('The time to start the controller has passed.')

        sleep(0.5)
        self.assertIsNone(MainDB.get_user(user), msg='the unreachable user has been deleted')

        self.sender.merge()
        self.controller.merge()

    @patch('lucky_bot.receiver.input_mq.test_func')
    def test_exception_in_the_imq(self, func, bot):
        func.side_effect = TestException('boom')
        bot.send_message.side_effect = self.exception
        user = '142'
        MainDB.add_user(user)
        OutputQueue.add_message(user, 'please die')

        self.controller.start()
        self.sender.start()
        if not SENDER_IS_STOPPED.wait(10):
            self.sender.merge()
            raise TestException('The time to stop the sender has passed.')
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.controller.merge()
            raise TestException('The time to stop the controller has passed.')

        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(IMQException, self.sender.merge)
        self.controller.merge()
