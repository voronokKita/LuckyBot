""" python -m unittest tests.units.test_webhook """
from unittest.mock import patch, Mock

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED
from lucky_bot.helpers.constants import (
    TestException, ThreadException, REPLIT, PORT,
    API, WEBHOOK_SECRET, WEBHOOK_ENDPOINT,
)

from tests.presets import ThreadTestTemplate


def mock_ngrok():
    tunnel = Mock()
    tunnel.public_url = 'http://example.com'
    ngrok = Mock()
    ngrok.connect.return_value = tunnel
    return ngrok


def mock_telebot():
    instance = Mock()
    instance.set_webhook.return_value = True
    TeleBot = Mock()
    TeleBot.return_value = instance
    return TeleBot


@patch('lucky_bot.webhook.TeleBot', new_callable=mock_telebot)
@patch('lucky_bot.webhook.ngrok', new_callable=mock_ngrok)
class TestWebhookBase(ThreadTestTemplate):
    thread_class = WebhookThread
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    def test_webhook_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_webhook_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_webhook_tunnel(self, ngrok, *args):
        self.assertFalse(REPLIT)

        self.thread_obj._make_tunnel()
        self.thread_obj._close_tunnel()

        ngrok.connect.assert_called_once_with(PORT, proto='http', bind_tls=True)
        self.assertEqual(self.thread_obj.webhook_url, 'http://example.com' + WEBHOOK_ENDPOINT)
        ngrok.disconnect.assert_called_once_with('http://example.com')
        ngrok.kill.assert_called_once()

    def test_setting_webhook(self, foo, TeleBot):
        self.thread_obj.webhook_url = 'http://example.com/hook'
        self.thread_obj._set_webhook()
        self.thread_obj._remove_webhook()

        self.assertEqual(TeleBot.call_count, 3)
        TeleBot.assert_called_with(API, threaded=False)

        instance = TeleBot()
        self.assertEqual(instance.remove_webhook.call_count, 2)
        instance.set_webhook.assert_called_once_with(
            url=self.thread_obj.webhook_url,
            max_connections=10,
            secret_token=WEBHOOK_SECRET,
        )

    def test_setting_tunnel_and_webhook_exception(self, ngrok, TeleBot):
        self.assertFalse(REPLIT)
        TeleBot().set_webhook.return_value = False

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        ngrok.connect.assert_called_once()
        self.assertIsNotNone(self.thread_obj.webhook_url)
        self.assertEqual(TeleBot.call_count, 3)

        instance = TeleBot()
        self.assertEqual(instance.remove_webhook.call_count, 1)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
