""" python -m unittest tests.units.test_webhook """
from unittest.mock import patch

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED

from tests.presets import ThreadTestTemplate


class TestWebhookBase(ThreadTestTemplate):
    thread_class = WebhookThread
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    def test_webhook_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_webhook_exception_case(self, test_exception):
        super().exception_case(test_exception)
