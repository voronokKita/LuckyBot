""" python -m unittest tests.units.test_input_controller """
from unittest.mock import patch

from lucky_bot.controller import ControllerThread
from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED

from tests.presets import ThreadTestTemplate


class TestInputControllerBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    def test_input_controller_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_input_controller_exception_case(self, test_exception):
        super().exception_case(test_exception)
