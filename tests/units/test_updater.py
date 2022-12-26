""" python -m unittest tests.units.test_updater """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.constants import TestException
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, EXIT_SIGNAL
from lucky_bot.updater import UpdaterThread


class UpdaterTestException(Exception):
    ...


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.updater = UpdaterThread()

    def tearDown(self):
        if self.updater.is_alive():
            EXIT_SIGNAL.set()
            self.updater.join(3)

    def test_updater_threading(self):
        self.updater.start()

        if UPDATER_IS_RUNNING.wait(10):
            EXIT_SIGNAL.set()
            sleep(0.01)
            self.updater.stop()
            self.assertFalse(self.updater.is_alive())

        else:
            raise UpdaterTestException('The time to start the updater has passed.')

    @patch('lucky_bot.updater.UpdaterThread._test_exception')
    def test_updater_threading_exception(self, mock_exception):
        mock_exception.side_effect = TestException('boom')
        self.updater.start()

        if UPDATER_IS_RUNNING.wait(10):
            self.assertRaises(TestException, self.updater.stop)
            self.assertFalse(self.updater.is_alive())
        else:
            raise UpdaterTestException('The time to start the updater has passed.')
