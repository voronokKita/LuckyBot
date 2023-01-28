""" python -m unittest tests.integration.controller.test_parser_with_db """
from lucky_bot.helpers.constants import DatabaseException
from lucky_bot import MainDB
from lucky_bot.controller import parser

from tests.presets import MainDBTemplate


class TestParserWithMainDB(MainDBTemplate):
    def test_parser_insert(self):
        uid = 1
        MainDB.add_user(uid)

        self.assertEqual(parser.parse_note_and_insert(uid, 'hello'), 'Saved.')

        q = MainDB.get_user_note(uid, 1)
        self.assertIsNotNone(q)
        self.assertEqual(q.text, 'hello')

    def test_parser_update(self):
        uid = 2
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'hello')

        self.assertEqual(parser.parse_note_and_update(uid, 'world', 1), 'Updated.')

        q = MainDB.get_user_note(uid, 1)
        self.assertIsNotNone(q)
        self.assertEqual(q.text, 'world')

    def test_parser_update_wrong_number(self):
        uid = 3
        MainDB.add_user(uid)
        self.assertEqual(
            parser.parse_note_and_update(uid, 'foobar', 1),
            'Error: wrong note number.'
        )


class TestParserWithMainDBExceptions(MainDBTemplate):
    def test_parser_insert_exception(self):
        self.assertRaises(DatabaseException, parser.parse_note_and_insert, bool, 123)

    def test_parser_update_exception(self):
        uid = 4
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'hello')
        self.assertRaises(DatabaseException, parser.parse_note_and_update, uid, bool, 1)
