""" python -m unittest tests.units.test_webhook """
from unittest.mock import patch, Mock

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED
from lucky_bot.helpers.constants import TestException, REPLIT, PORT, WEBHOOK_ENDPOINT

from tests.presets import ThreadTestTemplate

# TODO mock normal start

class TestWebhookBase(ThreadTestTemplate):
    thread_class = WebhookThread
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    def test_webhook_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_webhook_exception_case(self, test_exception):
        super().exception_case(test_exception)

    @patch('lucky_bot.webhook.ngrok')
    def test_webhook_tunnel(self, ngrok):
        self.assertFalse(REPLIT)

        tunnel = Mock()
        tunnel.public_url = 'http://example.com'
        ngrok.connect.return_value = tunnel

        self.thread_obj._make_tunnel()
        self.thread_obj._close_tunnel()

        ngrok.connect.assert_called_once_with(PORT, proto='http', bind_tls=True)
        self.assertEqual(self.thread_obj.webhook_url, 'http://example.com' + WEBHOOK_ENDPOINT)
        ngrok.disconnect.assert_called_once_with('http://example.com')
        ngrok.kill.assert_called_once()

