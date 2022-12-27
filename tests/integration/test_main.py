""" python -m unittest tests.integration.test_main """
import threading
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.signals import ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL


class MainTestException(Exception):
    ...


class TestMain(unittest.TestCase):
    def setUp(self):
        from main import MainAsThread
        self.main_thread = MainAsThread()

    def tearDown(self):
        if not EXIT_SIGNAL:
            EXIT_SIGNAL.set()
        if self.main_thread.is_alive():
            self.main_thread.stop()

    def test_main_integrity(self):
        self.main_thread.start()

        if ALL_THREADS_ARE_GO.wait(5):
            EXIT_SIGNAL.set()
        else:
            raise MainTestException('The time to start the threads has passed.')

        if ALL_DONE_SIGNAL.wait(10):
            sleep(0.01)
            self.main_thread.join(10)
            self.assertFalse(self.main_thread.is_alive())
        else:
            raise MainTestException('The time to finish the work has passed.')

    @patch('lucky_bot.updater.UpdaterThread._set_the_signal')
    def broken_main_threads_timeout(self, mock_signal):
        mock_signal.side_effect = Exception('boom')

        self.main_thread.start()
        print('A')
        if ALL_THREADS_ARE_GO.wait(5):
            print('B')
        else:
            print('C')

        EXIT_SIGNAL.set()
        mock_signal.assert_called_once()
        print('D')
