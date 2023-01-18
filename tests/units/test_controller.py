""" python -m unittest tests.units.test_controller """
import unittest
from unittest.mock import patch, Mock
from time import sleep

import telebot

from lucky_bot.helpers.constants import (
    TestException, ControllerException,
    TelebotHandlerException, PROJECT_DIR,
)
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.controller.bot_handlers import TEXT_HELLO, TEXT_HELP
from lucky_bot.controller import ControllerThread
from lucky_bot import BOT

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


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


@patch('lucky_bot.controller.controller.ControllerThread._test_controller_cycle')
@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.ControllerThread.respond')
@patch('lucky_bot.controller.controller.InputQueue')
class TestSender(ThreadSmallTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    other_signals = [INCOMING_MESSAGE]

    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        super().setUp()
        self.msg_obj1 = Mock()
        self.msg_obj2 = Mock()
        self.msg_obj3 = Mock()

    def test_sender_normal_message(self, mock_InputQueue, respond, bot, controller_cycle):
        self.msg_obj1.data = '/sender delete 42'
        self.msg_obj2.data = self.telegram_request
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj1, self.msg_obj2, None]
        INCOMING_MESSAGE.set()

        self.thread_obj.start()
        if not CONTROLLER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the controller has passed.')

        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        respond.delete_user.assert_called_once_with(42)
        bot.process_new_updates.assert_called_once()
        self.assertEqual(mock_InputQueue.delete_message.call_count, 2, msg='first')
        controller_cycle.assert_not_called()

        self.msg_obj3.data = '/sender delete 404'
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj3, None]
        INCOMING_MESSAGE.set()
        sleep(0.2)
        self.assertFalse(INCOMING_MESSAGE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(respond.delete_user.call_count, 2, msg='cycle')
        bot.process_new_updates.assert_called_once()
        self.assertEqual(mock_InputQueue.delete_message.call_count, 3, msg='cycle')
        controller_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        INCOMING_MESSAGE.set()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.thread_obj.merge()
        controller_cycle.assert_called_once()

    def test_controller_exception_in_message_process(self, mock_InputQueue, respond, bot, controller_cycle):
        self.msg_obj1.data = self.telegram_request
        mock_InputQueue.get_first_message.side_effect = [self.msg_obj1, None]
        bot.process_new_updates.side_effect = TestException('boom')

        self.thread_obj.start()
        if not CONTROLLER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the controller has passed.')

        self.assertFalse(CONTROLLER_IS_RUNNING.is_set(), msg='exception before this signal')
        controller_cycle.assert_not_called()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(TelebotHandlerException, self.thread_obj.merge)


@patch('lucky_bot.controller.controller.BOT')
@patch('lucky_bot.controller.controller.ControllerThread.respond')
class TestControllerCallToResponder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        self.controller = ControllerThread()
        self.msg_obj = Mock()

    def test_internal_sender_delete(self, respond, *args):
        self.msg_obj.data = '/sender delete 42'
        self.controller._process_the_message(self.msg_obj)
        respond.delete_user.assert_called_once_with(42)

    def test_telegram_message(self, arg, bot):
        self.msg_obj.data = self.telegram_request
        self.controller._process_the_message(self.msg_obj)
        bot.process_new_updates.assert_called_once()

    def test_telegram_message_exception(self, arg, bot):
        self.msg_obj.data = self.telegram_request
        bot.process_new_updates.side_effect = TestException('boom')

        self.assertRaises(TelebotHandlerException,
                          self.controller._process_the_message,
                          self.msg_obj)


@patch('lucky_bot.controller.bot_handlers.parser')
@patch('lucky_bot.controller.bot_handlers.respond')
class TestBotHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.uid = 1266575762
        cls.username = 'john_doe'
        fixtures = PROJECT_DIR / 'tests' / 'fixtures'
        with open(fixtures / 'telegram_request.json') as f:
            cls.telegram_text = f.read().strip()
        with open(fixtures / 'telegram_start.json') as f:
            cls.telegram_start = f.read().strip()
        with open(fixtures / 'telegram_help.json') as f:
            cls.telegram_help = f.read().strip()
        with open(fixtures / 'telegram_add.json') as f:
            cls.telegram_add = f.read().strip()
        with open(fixtures / 'telegram_add_blank.json') as f:
            cls.telegram_add_blank = f.read().strip()
        with open(fixtures / 'telegram_update.json') as f:
            cls.telegram_update = f.read().strip()
        with open(fixtures / 'telegram_update_wrong.json') as f:
            cls.telegram_update_wrong = f.read().strip()
        with open(fixtures / 'telegram_delete.json') as f:
            cls.telegram_delete = f.read().strip()
        with open(fixtures / 'telegram_delete_wrong.json') as f:
            cls.telegram_delete_wrong = f.read().strip()

    def test_start_cmd_exception(self, respond, *args):
        respond.delete_user.side_effect = TestException('boom')
        update = telebot.types.Update.de_json(self.telegram_start)
        self.assertRaises(TestException, BOT.process_new_updates, [update])

    def test_start_cmd(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_start)
        BOT.process_new_updates([update])
        respond.delete_user.assert_called_once_with(self.uid, start_cmd=True)
        msg = TEXT_HELLO.format(username=self.username, help=TEXT_HELP)
        respond.send_message.assert_called_once_with(self.uid, msg)

    def test_help_cmd(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_text)
        BOT.process_new_updates([update])
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

        update = telebot.types.Update.de_json(self.telegram_help)
        BOT.process_new_updates([update])
        respond.send_message.assert_called_with(self.uid, TEXT_HELP)
        self.assertEqual(respond.send_message.call_count, 2)

    def test_add_cmd(self, respond, parser):
        text = 'some text'
        parser.parse_note_and_insert.return_value = 'Done add.'
        update = telebot.types.Update.de_json(self.telegram_add)
        BOT.process_new_updates([update])

        parser.parse_note_and_insert.assert_called_once_with(self.uid, text)
        respond.send_message.assert_called_with(self.uid, 'Done add.')

    def test_add_cmd_blank(self, respond, parser):
        update = telebot.types.Update.de_json(self.telegram_add_blank)
        BOT.process_new_updates([update])

        parser.parse_note_and_insert.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

    def test_update_cmd(self, respond, parser):
        note_num = '1'
        text = 'new text'
        parser.parse_note_and_update.return_value = 'Done update.'
        update = telebot.types.Update.de_json(self.telegram_update)
        BOT.process_new_updates([update])

        parser.parse_note_and_update.assert_called_once_with(self.uid, text, note_num)
        respond.send_message.assert_called_with(self.uid, 'Done update.')

    def test_update_cmd_wrong(self, respond, parser):
        update = telebot.types.Update.de_json(self.telegram_update_wrong)
        BOT.process_new_updates([update])

        parser.parse_note_and_update.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

    def test_delete_cmd(self, respond, *args):
        note_num1 = '1'
        note_num2 = '2'
        update = telebot.types.Update.de_json(self.telegram_delete)
        BOT.process_new_updates([update])

        respond.delete_notes.assert_called_with(self.uid, [note_num1, note_num2])

    def test_delete_cmd_wrong(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_delete_wrong)
        BOT.process_new_updates([update])

        respond.delete_notes.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)
