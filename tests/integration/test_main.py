""" python -m unittest tests.integration.test_main """
import unittest
from unittest.mock import Mock, patch

from lucky_bot.helpers.constants import MainException, TestException, ThreadException
from lucky_bot.helpers.signals import (
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
    RECEIVER_IS_RUNNING, CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
)
from main import MainAsThread

from tests.presets import mock_ngrok, mock_telebot, mock_serving, SIGNALS


@patch('lucky_bot.updater.updater.Updater.works')
@patch('lucky_bot.updater.updater.UpdaterThread._time_to_wait', Mock(return_value=100))
@patch('lucky_bot.controller.controller.Controller.check_new_messages')
@patch('lucky_bot.sender.output_dispatcher.BOT')
@patch('lucky_bot.sender.sender.Sender.process_outgoing_messages')
@patch('lucky_bot.receiver.receiver.Receiver._remove_webhook')
@patch('lucky_bot.receiver.receiver.Receiver.start_server', new_callable=mock_serving)
@patch('lucky_bot.receiver.receiver.BOT', new_callable=mock_telebot)
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestMain(unittest.TestCase):
    def setUp(self):
        self.main_thread = MainAsThread()

    def tearDown(self):
        if self.main_thread.is_alive():
            self.main_thread.merge()
        [signal.clear() for signal in SIGNALS if signal.is_set()]
        self.assertFalse(self.main_thread.is_alive())

    def test_main_integrity(self, *args):
        self.main_thread.start()

        signals = [
            {'name': 'sender', 'signal': SENDER_IS_RUNNING},
            {'name': 'updater', 'signal': UPDATER_IS_RUNNING},
            {'name': 'controller', 'signal': CONTROLLER_IS_RUNNING},
            {'name': 'receiver', 'signal': RECEIVER_IS_RUNNING},
            {'name': 'all threads are go', 'signal': ALL_THREADS_ARE_GO},
            {'name': 'finished the work', 'signal': ALL_DONE_SIGNAL},
        ]
        for stage in signals:
            if stage['signal'].wait(10):
                if stage['name'] == 'all threads are go':
                    EXIT_SIGNAL.set()
            else:
                raise TestException(f'Stage Timeout: {stage["name"]}')

        self.main_thread.merge()

    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._set_the_signal')
    def test_main_threads_timeout(self, mock_signal, *args):
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(10):
            raise TestException('Timeout: exit signal not called.')
        if not ALL_DONE_SIGNAL.wait(10):
            raise TestException('Timeout: all_done signal not called.')

        # exception raised from main
        self.assertRaises(MainException, self.main_thread.merge)


    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_before_signal')
    def test_main_threads_error_before_signal(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(10):
            raise TestException('Timeout: exit signal not called.')
        if not ALL_DONE_SIGNAL.wait(10):
            raise TestException('Timeout: all_done signal not called.')

        # exception in ThreadTemplate
        self.assertRaises(TestException, self.main_thread.merge)

    @patch('main.TREAD_RUNNING_TIMEOUT', 0.1)
    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_main_threads_error_after_signal(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        self.main_thread.start()
        if not EXIT_SIGNAL.wait(10):
            raise TestException('Timeout: exit signal not called.')
        if not ALL_DONE_SIGNAL.wait(10):
            raise TestException('Timeout: all_done signal not called.')

        # exception in specific thread
        self.assertRaises(ThreadException, self.main_thread.merge)
