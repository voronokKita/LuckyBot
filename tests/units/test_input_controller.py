""" python -m unittest tests.units.test_input_controller """
from unittest.mock import patch

from lucky_bot.input_controller import InputControllerThread
from lucky_bot.helpers.signals import INPUT_CONTROLLER_IS_RUNNING, INPUT_CONTROLLER_IS_STOPPED

from tests.presets import ThreadTestTemplate


class TestInputControllerBase(ThreadTestTemplate):
    thread_class = InputControllerThread
    is_running_signal = INPUT_CONTROLLER_IS_RUNNING
    is_stopped_signal = INPUT_CONTROLLER_IS_STOPPED

    def test_input_controller_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_input_controller_exception_case(self, test_exception):
        super().exception_case(test_exception)
