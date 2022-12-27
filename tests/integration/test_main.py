""" python -m unittest tests.integration.test_main """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.signals import (
    ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL,
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
)
from lucky_bot.helpers.constants import MainError, TestException


SIGNALS = [
    EXIT_SIGNAL, ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL,
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
]

class MainTestException(Exception):
    ...


class TestMain(unittest.TestCase):
    def setUp(self):
        from main import MainAsThread
        self.main_thread = MainAsThread()

    def tearDown(self):
        if self.main_thread.is_alive():
            self.main_thread.stop()
        self._clear_signals()

    @staticmethod
    def _clear_signals():
        [signal.clear() for signal in SIGNALS if signal.is_set()]

    def test_main_integrity(self):
        self.main_thread.start()

        if ALL_THREADS_ARE_GO.wait(5):
            EXIT_SIGNAL.set()
        else:
            raise MainTestException('The time to start the threads has passed.')

        if ALL_DONE_SIGNAL.wait(10):
            sleep(0.01)
            self.main_thread.stop()
        else:
            raise MainTestException('The time to finish the work has passed.')

        self.assertFalse(self.main_thread.is_alive())

    @patch('lucky_bot.updater.UpdaterThread._set_the_signal')
    def test_main_threads_timeout(self, mock_signal):
        self.main_thread.start()

        if ALL_THREADS_ARE_GO.wait(4):
            raise MainTestException('ERROR: the broken thread has started.')
        else:
            with self.assertRaises(MainError):
                self.main_thread.stop()

        mock_signal.assert_called_once()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(self.main_thread.is_alive())

    @patch('lucky_bot.updater.UpdaterThread._set_the_signal')
    def test_main_threads_error_before_signal(self, mock_signal):
        mock_signal.side_effect = TestException('boom')
        self.main_thread.start()

        if ALL_THREADS_ARE_GO.wait(4):
            raise MainTestException('ERROR: the broken thread has started.')
        else:
            with self.assertRaises((MainError, TestException)):
                self.main_thread.stop()

        mock_signal.assert_called_once()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(self.main_thread.is_alive())

    @patch('lucky_bot.updater.UpdaterThread._test_exception')
    def test_main_threads_error_after_signal(self, test_exception):
        test_exception.side_effect = TestException('boom')
        self.main_thread.start()

        if ALL_DONE_SIGNAL.wait(4):
            pass
        else:
            raise MainTestException('The time to start the threads has passed.')

        self.assertTrue(ALL_THREADS_ARE_GO.is_set())
        test_exception.assert_called_once()
        self.assertTrue(EXIT_SIGNAL.is_set())
        with self.assertRaises(TestException):
            self.main_thread.stop()
        self.assertFalse(self.main_thread.is_alive())
