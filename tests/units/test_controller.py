""" python -m unittest tests.units.test_controller """
from unittest.mock import patch

from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED, INCOMING_MESSAGE
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadTestTemplate


@patch('lucky_bot.controller.controller.ControllerThread._check_new_messages')
class TestControllerThreadBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE]

    def test_controller_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_controller_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_controller_forced_merge(self, *args):
        super().forced_merge()

