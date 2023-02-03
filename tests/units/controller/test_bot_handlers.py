""" python -m unittest tests.units.controller.test_bot_handlers """
import unittest
from unittest.mock import patch

import telebot

from lucky_bot.helpers.constants import TestException, PROJECT_DIR
from lucky_bot.helpers.signals import EXIT_SIGNAL
from lucky_bot.controller.bot_handlers import TEXT_HELLO, TEXT_HELP
from lucky_bot import BOT


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
        with open(fixtures / 'telegram_update.json') as f:
            cls.telegram_update = f.read().strip()
        with open(fixtures / 'telegram_delete.json') as f:
            cls.telegram_delete = f.read().strip()
        with open(fixtures / 'telegram_list.json') as f:
            cls.telegram_list = f.read().strip()
        with open(fixtures / 'telegram_show.json') as f:
            cls.telegram_show = f.read().strip()
        with open(fixtures / 'telegram_show_overload.json') as f:
            cls.telegram_show_overload = f.read().strip()

    def tearDown(self):
        if EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.clear()

    def test_start_cmd(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_start)
        BOT.process_new_updates([update])

        respond.delete_user.assert_called_once_with(self.uid, start_cmd=True)
        respond.add_user.assert_called_once_with(self.uid)

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

    def test_update_cmd(self, respond, parser):
        note_num = '1'
        text = 'new text'
        parser.parse_note_and_update.return_value = 'Done update.'

        update = telebot.types.Update.de_json(self.telegram_update)
        BOT.process_new_updates([update])

        parser.parse_note_and_update.assert_called_once_with(self.uid, text, note_num)
        respond.send_message.assert_called_with(self.uid, 'Done update.')

    def test_delete_cmd(self, respond, *args):
        note_num1 = '1'
        note_num2 = '2'

        update = telebot.types.Update.de_json(self.telegram_delete)
        BOT.process_new_updates([update])

        respond.delete_notes.assert_called_with(self.uid, [note_num1, note_num2])

    def test_list_cmd(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_list)
        BOT.process_new_updates([update])

        respond.send_list.assert_called_with(self.uid)

    def test_show_cmd(self, respond, *args):
        note_num = '1'
        update = telebot.types.Update.de_json(self.telegram_show)
        BOT.process_new_updates([update])

        respond.send_note.assert_called_once_with(self.uid, note_num)

    def test_show_cmd_overload(self, respond, *args):
        note_num = '1'
        update = telebot.types.Update.de_json(self.telegram_show_overload)
        BOT.process_new_updates([update])

        respond.send_note.assert_called_once_with(self.uid, note_num)


@patch('lucky_bot.controller.bot_handlers.parser')
@patch('lucky_bot.controller.bot_handlers.respond')
class TestBotHandlersExceptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.uid = 1266575762
        cls.username = 'john_doe'
        fixtures = PROJECT_DIR / 'tests' / 'fixtures'
        with open(fixtures / 'telegram_start.json') as f:
            cls.telegram_start = f.read().strip()
        with open(fixtures / 'telegram_add_blank.json') as f:
            cls.telegram_add_blank = f.read().strip()
        with open(fixtures / 'telegram_update_wrong.json') as f:
            cls.telegram_update_wrong = f.read().strip()
        with open(fixtures / 'telegram_delete_wrong.json') as f:
            cls.telegram_delete_wrong = f.read().strip()
        with open(fixtures / 'telegram_show_wrong.json') as f:
            cls.telegram_show_wrong = f.read().strip()

    def tearDown(self):
        if EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.clear()

    def test_start_cmd_exception(self, respond, *args):
        respond.delete_user.side_effect = TestException('boom')
        update = telebot.types.Update.de_json(self.telegram_start)

        self.assertRaises(TestException, BOT.process_new_updates, [update])

    def test_add_cmd_blank(self, respond, parser):
        update = telebot.types.Update.de_json(self.telegram_add_blank)
        BOT.process_new_updates([update])

        parser.parse_note_and_insert.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

    def test_update_cmd_wrong(self, respond, parser):
        update = telebot.types.Update.de_json(self.telegram_update_wrong)
        BOT.process_new_updates([update])

        parser.parse_note_and_update.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

    def test_delete_cmd_wrong(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_delete_wrong)
        BOT.process_new_updates([update])

        respond.delete_notes.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)

    def test_show_cmd_wrong(self, respond, *args):
        update = telebot.types.Update.de_json(self.telegram_show_wrong)
        BOT.process_new_updates([update])

        respond.send_note.assert_not_called()
        respond.send_message.assert_called_once_with(self.uid, TEXT_HELP)
