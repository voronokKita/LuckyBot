""" python -m unittest tests.integration.controller.test_parser_with_db """
from unittest.mock import MagicMock

from lucky_bot.helpers.constants import DatabaseException, TestException
from lucky_bot.helpers.misc import decrypt
from lucky_bot import MainDB
from lucky_bot.controller import parser

from tests.presets import MainDBTemplate


class TestParserWithMainDB(MainDBTemplate):
    def test_parser_insert(self):
        uid = '1'
        text = 'hello'
        MainDB.add_user(uid)

        self.assertEqual(parser.parse_note_and_insert(uid, text), 'Saved.')

        q = MainDB.get_user_note(uid, note_num=1)
        self.assertIsNotNone(q)
        self.assertEqual(decrypt(q.text), text)

    def test_parser_update(self):
        uid = '2'
        text1 = 'hello'
        text2 = 'world'
        MainDB.add_user(uid)
        MainDB.add_note(uid, text1)

        self.assertEqual(parser.parse_note_and_update(uid, text2, note_num=1), 'Updated.')

        q = MainDB.get_user_note(uid, note_num=1)
        self.assertIsNotNone(q)
        self.assertEqual(decrypt(q.text), text2)

    def test_parser_update_wrong_number(self):
        uid = '3'
        MainDB.add_user(uid)
        self.assertEqual(
            parser.parse_note_and_update(uid, 'foobar', 1),
            'Error: wrong note number.'
        )


class TestParserWithMainDBExceptions(MainDBTemplate):
    def test_parser_insert_exception(self):
        uid = MagicMock()
        uid.__str__.side_effect = TestException('boom')
        self.assertRaises(DatabaseException, parser.parse_note_and_insert, uid, 'null')

    def test_parser_update_exception(self):
        uid = '4'
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'hello')
        self.assertRaises(DatabaseException, parser.parse_note_and_update, uid, b'wrong data', 1)
