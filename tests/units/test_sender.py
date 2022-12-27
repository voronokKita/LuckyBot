""" python -m unittest tests.units.test_sender """
from unittest.mock import patch

from lucky_bot.sender import SenderThread
from lucky_bot.helpers.signals import SENDER_IS_RUNNING, SENDER_IS_STOPPED

from tests.presets import ThreadTestTemplate


class TestSenderBase(ThreadTestTemplate):
    thread_class = SenderThread
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def test_sender_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_sender_exception_case(self, test_exception):
        super().exception_case(test_exception)
