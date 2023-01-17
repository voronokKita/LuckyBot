""" python -m unittest tests.units.test_controller """
import unittest
from unittest.mock import patch, Mock

from lucky_bot.helpers.constants import PROJECT_DIR
from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED, INCOMING_MESSAGE
from lucky_bot.controller import ControllerThread

from tests.presets import ThreadTestTemplate


@patch('lucky_bot.controller.controller.ControllerThread._check_new_messages')
class TestControllerThreadBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE]

    def test_controller_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_controller_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_controller_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.controller.controller.BOT')
class TestControllerCallToResponder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = ControllerThread()
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        self.respond = Mock()
        self.controller.respond = self.respond
        self.msg_obj = Mock()

    def test_internal_sender_delete(self, *args):
        self.msg_obj.data = '/sender delete 42'
        self.controller._process_the_message(self.msg_obj)
        self.respond.delete_user.assert_called_once_with(42)

    def test_telegram_message(self, bot):
        self.msg_obj.data = self.telegram_request
        self.controller._process_the_message(self.msg_obj)
        bot.process_new_updates.assert_called_once()
