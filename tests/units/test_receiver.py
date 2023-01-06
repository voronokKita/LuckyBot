""" python -m unittest tests.units.test_receiver """
import unittest
from unittest.mock import patch, Mock

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED,
    EXIT_SIGNAL, NEW_TELEGRAM_MESSAGE,
)
from lucky_bot.helpers.constants import (
    TestException, ThreadException, FlaskException,
    REPLIT, PORT, WEBHOOK_SECRET,
    WEBHOOK_ENDPOINT, PROJECT_DIR,
)
from lucky_bot.flask_config import FLASK_APP
from lucky_bot.models.input_mq import InputQueue

from tests.presets import ThreadTestTemplate


def mock_ngrok():
    tunnel = Mock()
    tunnel.public_url = 'http://0.0.0.0'
    ngrok = Mock()
    ngrok.connect.return_value = tunnel
    return ngrok


def mock_telebot():
    bot = Mock()
    bot.set_webhook.return_value = True
    return bot


def mock_serving():
    def start_server(self=None):
        EXIT_SIGNAL.wait()
    return start_server


@patch('lucky_bot.webhook.WebhookThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.webhook.BOT', new_callable=mock_telebot)
@patch('lucky_bot.webhook.ngrok', new_callable=mock_ngrok)
class TestWebhook(ThreadTestTemplate):
    thread_class = WebhookThread
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED
    signals = [NEW_TELEGRAM_MESSAGE]

    def tearDown(self):
        if self.thread_obj.server:
            self.thread_obj.server.socket.close()
        super().tearDown()

    def test_webhook_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_webhook_normal_exception(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_webhook_forced_merge(self, *args):
        super().forced_merge()

    def test_webhook_tunnel(self, ngrok, *args):
        self.assertFalse(REPLIT)

        self.thread_obj._make_tunnel()
        self.thread_obj._close_tunnel()

        ngrok.connect.assert_called_once_with(PORT, proto='http', bind_tls=True)
        self.assertEqual(self.thread_obj.webhook_url, 'http://0.0.0.0' + WEBHOOK_ENDPOINT)
        ngrok.disconnect.assert_called_once_with('http://0.0.0.0')
        ngrok.kill.assert_called_once()

    def test_setting_webhook(self, foo, bot, *args):
        self.thread_obj.webhook_url = 'http://0.0.0.0/webhook'
        self.thread_obj._set_webhook()
        self.thread_obj._remove_webhook()

        self.assertEqual(bot.remove_webhook.call_count, 2)
        bot.set_webhook.assert_called_once_with(
            url=self.thread_obj.webhook_url,
            max_connections=10,
            secret_token=WEBHOOK_SECRET,
        )

    def test_tunnel_and_setting_webhook_exception(self, ngrok, bot, *args):
        self.assertFalse(REPLIT)
        bot.set_webhook.return_value = False

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        ngrok.connect.assert_called_once()
        self.assertIsNotNone(self.thread_obj.webhook_url)

        self.assertEqual(bot.remove_webhook.call_count, 1)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()

    def test_that_server_created(self, *args):
        self.assertIsNotNone(FLASK_APP)
        self.thread_obj._make_server()
        from werkzeug.serving import BaseWSGIServer
        self.assertIsInstance(self.thread_obj.server, BaseWSGIServer)

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    @patch('lucky_bot.webhook.WebhookThread._make_tunnel')
    def test_webhook_exception_before_tunnel(self, make_tunnel, remove_webhook, close_tunnel, *args):
        make_tunnel.side_effect = TestException('boom')

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNone(self.thread_obj.tunnel)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.server)
        self.assertFalse(self.thread_obj.serving)
        remove_webhook.assert_not_called()
        close_tunnel.assert_not_called()

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    @patch('lucky_bot.webhook.WebhookThread._set_webhook')
    def test_webhook_exception_after_tunnel(self, set_webhook, remove_webhook, close_tunnel, *args):
        set_webhook.side_effect = TestException('boom')

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNotNone(self.thread_obj.tunnel)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.server)
        self.assertFalse(self.thread_obj.serving)
        remove_webhook.assert_not_called()
        close_tunnel.assert_called_once()

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    @patch('lucky_bot.webhook.WebhookThread._make_server')
    def test_webhook_exception_after_webhook_setup(self, make_server, remove_webhook, close_tunnel, *args):
        make_server.side_effect = TestException('boom')

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNotNone(self.thread_obj.tunnel)
        self.assertTrue(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.server)
        self.assertFalse(self.thread_obj.serving)
        self.assertEqual(remove_webhook.call_count, 2)
        close_tunnel.assert_called_once()

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_webhook_exception_after_making_server(self, test_exception, remove_webhook, close_tunnel, *args):
        test_exception.side_effect = TestException('boom')

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNotNone(self.thread_obj.tunnel)
        self.assertTrue(self.thread_obj.webhook)
        self.assertIsNotNone(self.thread_obj.server)
        self.assertFalse(self.thread_obj.serving)
        self.assertEqual(remove_webhook.call_count, 2)
        close_tunnel.assert_called_once()

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    @patch('lucky_bot.webhook.WebhookThread._test_exception_after_serving')
    def test_webhook_exception_after_server_start(self, test_exception, remove_webhook, close_tunnel, *args):
        test_exception.side_effect = TestException('boom')

        self.thread_obj.start()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to raise exception in the webhook has passed.')

        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNotNone(self.thread_obj.tunnel)
        self.assertTrue(self.thread_obj.webhook)
        self.assertIsNotNone(self.thread_obj.server)
        self.assertEqual(remove_webhook.call_count, 2)
        close_tunnel.assert_called_once()

        self.assertFalse(self.thread_obj.serving)

    @patch('lucky_bot.webhook.WebhookThread._close_tunnel')
    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    def test_complete_webhook_start_and_merge(self, remove_webhook, close_tunnel, *args):
        self.thread_obj.start()
        EXIT_SIGNAL.set()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the webhook has passed.')

        self.thread_obj.merge()
        self.assertFalse(self.thread_obj.is_alive())
        self.assertIsNotNone(self.thread_obj.tunnel)
        self.assertTrue(self.thread_obj.webhook)
        self.assertIsNotNone(self.thread_obj.server)
        self.assertFalse(self.thread_obj.serving)
        self.assertEqual(remove_webhook.call_count, 2)
        close_tunnel.assert_called_once()
        self.assertIn('closed', str(self.thread_obj.server.socket))


@patch('lucky_bot.flask_config.InputQueue')
class TestFlaskApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        FLASK_APP.config['ENV'] = 'development'
        FLASK_APP.config['TESTING'] = True
        FLASK_APP.config['DEBUG'] = True
        self.client = FLASK_APP.test_client()

    def tearDown(self):
        signals = [EXIT_SIGNAL, NEW_TELEGRAM_MESSAGE]
        [signal.clear() for signal in signals if signal.is_set()]
        FLASK_APP.config['ENV'] = 'production'
        FLASK_APP.config['TESTING'] = False
        FLASK_APP.config['DEBUG'] = False

    def test_flask_app(self, *args):
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'pong')

    def test_flask_app_wrong_request(self, *args):
        response = self.client.post(WEBHOOK_ENDPOINT, data=r'junk')
        self.assertEqual(response.status_code, 400)

    def test_flask_app_normal_request(self, *args):
        response = self.client.post(
            WEBHOOK_ENDPOINT,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertEqual(response.status_code, 200)

    @patch('lucky_bot.flask_config.test_exception')
    @patch('lucky_bot.flask_config.test_flag')
    def test_flask_app_exception_case(self, test_flag, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        with self.assertRaises(FlaskException):
            response = self.client.post(
                WEBHOOK_ENDPOINT,
                headers={'Content-Type': 'application/json',
                         'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
                data=self.telegram_request.encode(),
            )
        test_flag.assert_called_once()
        self.assertTrue(EXIT_SIGNAL.is_set())


class TestReceiverMessageQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        InputQueue.set_up()
        self.client = FLASK_APP.test_client()

    def tearDown(self):
        InputQueue.tear_down()
        signals = [EXIT_SIGNAL, NEW_TELEGRAM_MESSAGE]
        [signal.clear() for signal in signals if signal.is_set()]

    def test_input_queue_works(self):
        response = self.client.post(
            WEBHOOK_ENDPOINT,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertEqual(response.status_code, 200)

        msg_obj = InputQueue.get_first_message()
        self.assertIsNotNone(msg_obj)

        InputQueue.delete_message(msg_obj)
        result = InputQueue.get_first_message()
        self.assertIsNone(result)
