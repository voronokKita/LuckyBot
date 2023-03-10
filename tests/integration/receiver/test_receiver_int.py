""" python -m unittest tests.integration.receiver.test_receiver_int """
import os
from unittest.mock import patch

import requests

from lucky_bot.helpers.constants import (
    TestException, ADDRESS, PORT, PROJECT_DIR,
    WEBHOOK_SECRET, WEBHOOK_ENDPOINT,
)
from lucky_bot.helpers.signals import (
    RECEIVER_IS_RUNNING, RECEIVER_IS_STOPPED,
    EXIT_SIGNAL, INCOMING_MESSAGE,
)
from lucky_bot.receiver import InputQueue
from lucky_bot.receiver import FLASK_APP
from lucky_bot.receiver import ReceiverThread

from tests.presets import ThreadSmallTestTemplate, mock_ngrok, mock_telebot


@patch('lucky_bot.receiver.receiver.BOT', new_callable=mock_telebot)
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestReceiverServing(ThreadSmallTestTemplate):
    thread_class = ReceiverThread
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED

    @classmethod
    def setUpClass(cls):
        cls.url = f'http://{ADDRESS}:{PORT}{WEBHOOK_ENDPOINT}'
        os.environ['no_proxy'] = '0.0.0.0,127.0.0.1,localhost,example.com'

        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        FLASK_APP.config['ENV'] = 'development'
        FLASK_APP.config['TESTING'] = True
        FLASK_APP.config['DEBUG'] = True
        InputQueue.set_up()
        super().setUp()

    def tearDown(self):
        if self.thread_obj.receiver.server:
            self.thread_obj.receiver.server.socket.close()
        super().tearDown()
        InputQueue.tear_down()
        FLASK_APP.config['ENV'] = 'production'
        FLASK_APP.config['TESTING'] = False
        FLASK_APP.config['DEBUG'] = False

    def test_receiver_integration(self, ngrok, bot):
        self.thread_obj.start()

        # assert normal start
        if not RECEIVER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the receiver has passed.')

        ngrok.connect.assert_called_once()
        self.assertEqual(self.thread_obj.receiver.webhook_url, 'http://0.0.0.0' + WEBHOOK_ENDPOINT)
        bot.remove_webhook.assert_called_once()
        bot.set_webhook.assert_called_once()
        self.assertTrue(self.thread_obj.receiver.webhook)
        self.assertIsNotNone(self.thread_obj.receiver.server)
        self.assertTrue(self.thread_obj.receiver.serving)

        # ping-pong
        response = requests.get(f'http://{ADDRESS}:{PORT}/ping')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='ping-pong')
        self.assertEqual(response.status_code, 200, msg='ping-pong')
        self.assertEqual(response.text, 'pong')

        # tg message
        response = requests.post(
            self.url,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='post request')
        self.assertEqual(response.status_code, 200, msg='post request')
        if not INCOMING_MESSAGE.wait(10):
            self.thread_obj.merge()
            raise TestException('The request code 200, but there is no signal...')

        # input message queue
        result = InputQueue.get_first_message()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], self.telegram_request)
        InputQueue.delete_message(result[0])
        self.assertIsNone(InputQueue.get_first_message())

        # wrong request
        response = requests.post(self.url, data=r'junk')
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(InputQueue.get_first_message())

        # assert normal shutdown
        self.thread_obj.receiver.server.shutdown()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        self.assertFalse(self.thread_obj.receiver.serving)
        self.assertEqual(bot.remove_webhook.call_count, 2)
        self.assertFalse(self.thread_obj.receiver.webhook)
        self.assertIsNone(self.thread_obj.receiver.webhook_url)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertIsNone(self.thread_obj.receiver.tunnel)

        self.thread_obj.merge()
        self.assertIsNone(self.thread_obj.receiver.server)

    @patch('lucky_bot.receiver.flask_config.test_exception')
    def test_receiver_exception_in_flask_app(self, test_exception, ngrok, bot):
        test_exception.side_effect = TestException('boom')

        self.thread_obj.start()
        if not RECEIVER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the receiver has passed.')
        self.assertTrue(self.thread_obj.receiver.serving)

        response = requests.post(
            self.url,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        if not EXIT_SIGNAL.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to send an exit signal has passed.')

        # There is no way that EXIT_SIGNAL itself can stop the receiver thread
        self.assertTrue(self.thread_obj.receiver.serving)
        self.assertFalse(RECEIVER_IS_STOPPED.is_set())
        self.assertTrue(self.thread_obj.is_alive())

        self.thread_obj.receiver.server.shutdown()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        self.thread_obj.merge()
