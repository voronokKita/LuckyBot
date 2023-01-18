""" python -m unittest tests.units.receiver.test_flask_app """
import unittest
from unittest.mock import patch

from lucky_bot.helpers.signals import EXIT_SIGNAL, INCOMING_MESSAGE
from lucky_bot.helpers.constants import (
    TestException, FlaskException, PROJECT_DIR,
    WEBHOOK_SECRET, WEBHOOK_ENDPOINT,
)
from lucky_bot.receiver import FLASK_APP


@patch('lucky_bot.receiver.flask_config.InputQueue')
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
        signals = [EXIT_SIGNAL, INCOMING_MESSAGE]
        [signal.clear() for signal in signals if signal.is_set()]
        FLASK_APP.config['ENV'] = 'production'
        FLASK_APP.config['TESTING'] = False
        FLASK_APP.config['DEBUG'] = False

    def test_flask_app_ping(self, *args):
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'pong')

    def test_flask_app_normal_request(self, imq):
        response = self.client.post(
            WEBHOOK_ENDPOINT,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertEqual(response.status_code, 200)
        imq.add_message.assert_called_once()

    def test_flask_app_wrong_request(self, *args):
        response = self.client.post(WEBHOOK_ENDPOINT, data=r'junk')
        self.assertEqual(response.status_code, 400)

    @patch('lucky_bot.receiver.flask_config.get_message_data')
    def test_flask_app_get_msg_exception(self, get_message, *args):
        get_message.side_effect = TestException('boom')
        with self.assertRaises(FlaskException):
            response = self.client.post(WEBHOOK_ENDPOINT, data=r'junk')
        self.assertTrue(EXIT_SIGNAL.is_set())

    @patch('lucky_bot.receiver.flask_config.test_exception')
    def test_flask_app_save_msg_exception(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        with self.assertRaises(FlaskException):
            response = self.client.post(
                WEBHOOK_ENDPOINT,
                headers={'Content-Type': 'application/json',
                         'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
                data=self.telegram_request.encode(),
            )
        self.assertTrue(EXIT_SIGNAL.is_set())
