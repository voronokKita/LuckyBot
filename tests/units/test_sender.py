""" python -m unittest tests.units.test_sender """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.sender import SenderThread
from lucky_bot.helpers.constants import TestException
from lucky_bot.helpers.signals import SENDER_IS_RUNNING, EXIT_SIGNAL


SIGNALS = [EXIT_SIGNAL, SENDER_IS_RUNNING]

class SenderTestException(Exception):
    ...


class TestSender(unittest.TestCase):
    def setUp(self):
        self.sender = SenderThread()

    def tearDown(self):
        if self.sender.is_alive():
            EXIT_SIGNAL.set()
            self.sender.join(3)
        self._clear_signals()

    @staticmethod
    def _clear_signals():
        [signal.clear() for signal in SIGNALS if signal.is_set()]

    def test_sender_threading(self):
        self.sender.start()

        if SENDER_IS_RUNNING.wait(10):
            EXIT_SIGNAL.set()
            sleep(0.01)
            self.sender.stop()
            self.assertFalse(self.sender.is_alive())

        else:
            raise SenderTestException('The time to start the sender has passed.')

    @patch('lucky_bot.sender.SenderThread._test_exception')
    def test_sender_threading_exception(self, mock_exception):
        mock_exception.side_effect = TestException('boom')
        self.sender.start()

        if SENDER_IS_RUNNING.wait(10):
            self.assertRaises(TestException, self.sender.stop)
            self.assertFalse(self.sender.is_alive())
        else:
            raise SenderTestException('The time to start the sender has passed.')

