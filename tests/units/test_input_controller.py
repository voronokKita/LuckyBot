""" python -m unittest tests.units.test_input_controller """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.helpers.constants import TestException
from lucky_bot.helpers.signals import INPUT_CONTROLLER_IS_RUNNING, EXIT_SIGNAL
from lucky_bot.input_controller import InputControllerThread


class InputControllerTestException(Exception):
    ...


class TestInputController(unittest.TestCase):
    def setUp(self):
        self.input_controller = InputControllerThread()

    def tearDown(self):
        if self.input_controller.is_alive():
            EXIT_SIGNAL.set()
            self.input_controller.join(3)

    def test_input_controller_threading(self):
        self.input_controller.start()

        if INPUT_CONTROLLER_IS_RUNNING.wait(10):
            EXIT_SIGNAL.set()
            sleep(0.01)
            self.input_controller.stop()
            self.assertFalse(self.input_controller.is_alive())

        else:
            raise InputControllerTestException('The time to start the input controller has passed.')

    @patch('lucky_bot.input_controller.InputControllerThread._test_exception')
    def test_input_controller_threading_exception(self, mock_exception):
        mock_exception.side_effect = TestException('boom')
        self.input_controller.start()

        if INPUT_CONTROLLER_IS_RUNNING.wait(10):
            self.assertRaises(TestException, self.input_controller.stop)
            self.assertFalse(self.input_controller.is_alive())
        else:
            raise InputControllerTestException('The time to start the input controller has passed.')
