""" python -m unittest tests.integration.receiver.test_flask_with_imq """
import unittest

from lucky_bot.helpers.constants import PROJECT_DIR, WEBHOOK_SECRET, WEBHOOK_ENDPOINT
from lucky_bot.helpers.signals import EXIT_SIGNAL, INCOMING_MESSAGE
from lucky_bot.receiver import InputQueue
from lucky_bot.receiver import FLASK_APP


class TestFlaskWithMessageQueue(unittest.TestCase):
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
        signals = [EXIT_SIGNAL, INCOMING_MESSAGE]
        [signal.clear() for signal in signals if signal.is_set()]

    def test_flask_with_imq_integration(self):
        self.assertIsNone(InputQueue.get_first_message())

        response = self.client.post(
            WEBHOOK_ENDPOINT,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertEqual(response.status_code, 200)

        result = InputQueue.get_first_message()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], self.telegram_request)

        InputQueue.delete_message(result[0])
        self.assertIsNone(InputQueue.get_first_message())
