""" python -m unittest tests.units.test_webhook """
import unittest
from unittest.mock import patch
from time import sleep

from lucky_bot.webhook import WebhookThread
from lucky_bot.helpers.constants import TestException
from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, EXIT_SIGNAL


SIGNALS = [EXIT_SIGNAL, WEBHOOK_IS_RUNNING]

class WebhookTestException(Exception):
    ...


class TestWebhook(unittest.TestCase):
    def setUp(self):
        self.webhook = WebhookThread()

    def tearDown(self):
        if self.webhook.is_alive():
            EXIT_SIGNAL.set()
            self.webhook.join(3)
        self._clear_signals()

    @staticmethod
    def _clear_signals():
        [signal.clear() for signal in SIGNALS if signal.is_set()]

    def test_webhook_threading(self):
        self.webhook.start()

        if WEBHOOK_IS_RUNNING.wait(10):
            EXIT_SIGNAL.set()
            sleep(0.01)
            self.webhook.stop()
            self.assertFalse(self.webhook.is_alive())

        else:
            raise WebhookTestException('The time to start the webhook has passed.')

    @patch('lucky_bot.webhook.WebhookThread._test_exception')
    def test_webhook_threading_exception(self, mock_exception):
        mock_exception.side_effect = TestException('boom')
        self.webhook.start()

        if WEBHOOK_IS_RUNNING.wait(10):
            self.assertRaises(TestException, self.webhook.stop)
            self.assertFalse(self.webhook.is_alive())
        else:
            raise WebhookTestException('The time to start the webhook has passed.')
