""" python -m unittest tests.integration.test_main """
import unittest
from unittest.mock import patch

from lucky_bot.helpers.signals import (
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
    WEBHOOK_IS_RUNNING, CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
    WEBHOOK_IS_STOPPED, CONTROLLER_IS_STOPPED,
    UPDATER_IS_STOPPED, SENDER_IS_STOPPED,
)
from lucky_bot.helpers.constants import MainException, TestException, ThreadException
from main import MainAsThread

from tests.units.test_receiver import mock_ngrok, mock_telebot, mock_serving


@patch('lucky_bot.webhook.WebhookThread._remove_webhook')
@patch('lucky_bot.webhook.WebhookThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.webhook.TeleBot', new_callable=mock_telebot)
@patch('lucky_bot.webhook.ngrok', new_callable=mock_ngrok)
class TestMain(unittest.TestCase):
    signals = [
        ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
        WEBHOOK_IS_RUNNING, CONTROLLER_IS_RUNNING,
        UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
        WEBHOOK_IS_STOPPED, CONTROLLER_IS_STOPPED,
        UPDATER_IS_STOPPED, SENDER_IS_STOPPED,
    ]

    def setUp(self):
        self.main_thread = MainAsThread()

    def tearDown(self):
        if self.main_thread.is_alive():
            self.main_thread.merge()
        self._clear_signals()

    @classmethod
    def _clear_signals(cls):
        [signal.clear() for signal in cls.signals if signal.is_set()]

    def test_main_integrity(self, *args):
        self.main_thread.start()

        signals = [
            {'name': 'sender', 'signal': SENDER_IS_RUNNING},
            {'name': 'updater', 'signal': UPDATER_IS_RUNNING},
            {'name': 'input controller', 'signal': CONTROLLER_IS_RUNNING},
            {'name': 'webhook', 'signal': WEBHOOK_IS_RUNNING},
            {'name': 'all threads are go', 'signal': ALL_THREADS_ARE_GO},
            {'name': 'finish the work', 'signal': ALL_DONE_SIGNAL},
        ]
        for stage in signals:
            if stage['signal'].wait(10):
                if stage['name'] == 'all threads are go':
                    EXIT_SIGNAL.set()
            else:
                raise TestException(f'Stage Timeout: {stage["name"]}')

        self.main_thread.merge()
        self.assertFalse(self.main_thread.is_alive())

    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._set_the_signal')
    def test_main_threads_timeout(self, mock_signal, *args):
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(5):
            raise TestException('Timeout: exit signal not called.')

        self.assertRaises(MainException, self.main_thread.merge)
        self.assertTrue(ALL_DONE_SIGNAL.is_set())
        self.assertFalse(self.main_thread.is_alive())

    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_before_signal')
    def test_main_threads_error_before_signal(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(5):
            raise TestException('Timeout: exit signal not called.')

        test_exception.assert_called_once()
        self.assertRaises(ThreadException, self.main_thread.merge)
        self.assertTrue(ALL_DONE_SIGNAL.is_set())
        self.assertFalse(self.main_thread.is_alive())

    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_main_threads_error_after_signal(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(5):
            raise TestException('Timeout: exit signal not called.')

        test_exception.assert_called_once()
        self.assertRaises(ThreadException, self.main_thread.merge)
        self.assertTrue(ALL_DONE_SIGNAL.is_set())
        self.assertFalse(self.main_thread.is_alive())
