""" python -m unittest tests.integration.test_webhook_int """
import os
import unittest
from unittest.mock import patch

import requests

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED,
    EXIT_SIGNAL, NEW_TELEGRAM_MESSAGE,
)
from lucky_bot.helpers.constants import (
    TestException, ADDRESS, PORT,
    WEBHOOK_SECRET, WEBHOOK_ENDPOINT, PROJECT_DIR,
)
from lucky_bot.flask_config import FLASK_APP
from lucky_bot.models.input_mq import InputQueue

from tests.units.test_webhook import mock_ngrok, mock_telebot


@patch('lucky_bot.webhook.TeleBot', new_callable=mock_telebot)
@patch('lucky_bot.webhook.ngrok', new_callable=mock_ngrok)
class TestWebhookServing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['no_proxy'] = '0.0.0.0,127.0.0.1,localhost,example.com'

        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        FLASK_APP.config['ENV'] = 'development'
        FLASK_APP.config['TESTING'] = True
        FLASK_APP.config['DEBUG'] = True

        InputQueue.set_up()
        self.thread_obj = WebhookThread()

    def tearDown(self):
        if self.thread_obj.is_alive():
            self.thread_obj.merge()

        InputQueue.tear_down()
        self._clear_signals()
        FLASK_APP.config['ENV'] = 'production'
        FLASK_APP.config['TESTING'] = False
        FLASK_APP.config['DEBUG'] = False

    @classmethod
    def _clear_signals(cls):
        signals = [EXIT_SIGNAL, NEW_TELEGRAM_MESSAGE,
                   WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED]
        [signal.clear() for signal in signals if signal.is_set()]

    @patch('lucky_bot.webhook.WebhookThread._remove_webhook')
    def test_webhook_thread_server_sql_integration(self, remove_webhook, ngrok, TeleBot):
        self.thread_obj.start()

        # assert normal start
        if not WEBHOOK_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        ngrok.connect.assert_called_once()
        self.assertEqual(self.thread_obj.webhook_url, 'http://0.0.0.0' + WEBHOOK_ENDPOINT)

        remove_webhook.assert_called_once()
        TeleBot.assert_called_once()
        self.assertTrue(self.thread_obj.webhook)

        self.assertIsNotNone(self.thread_obj.server)
        self.assertTrue(self.thread_obj.serving)

        # ping-pong
        response = requests.get(f'http://{ADDRESS}:{PORT}/ping')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='ping-pong')
        self.assertEqual(response.status_code, 200, msg='ping-pong')
        self.assertEqual(response.text, 'pong')

        # tg message
        response = requests.post(
            f'http://{ADDRESS}:{PORT}{WEBHOOK_ENDPOINT}',
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='post request')
        self.assertEqual(response.status_code, 200, msg='post request')
        if not NEW_TELEGRAM_MESSAGE.wait(10):
            self.thread_obj.merge()
            raise TestException('The request code 200, but there is no signal...')

        # input message queue
        msg_obj = InputQueue.get_first_message()
        self.assertIsNotNone(msg_obj)

        # assert normal shutdown
        self.thread_obj._shutdown()
        if not WEBHOOK_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.assertFalse(self.thread_obj.serving)
        self.assertEqual(remove_webhook.call_count, 2)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()

        self.thread_obj.merge()
