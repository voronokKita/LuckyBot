""" python -m unittest tests.integration.controller.test_parser_with_db """
from lucky_bot import MainDB
from lucky_bot.controller import parser

from tests.presets import MainDBTemplate


class TestParserWithMainDB(MainDBTemplate):
    def test_parser_insert(self):
        uid = 1
        self.assertTrue(MainDB.add_user(uid))

        self.assertEqual(parser.parse_note_and_insert(uid, 'hello'), 'Saved.')

        q = MainDB.get_user_note(uid, 1)
        self.assertIsNotNone(q)
        self.assertEqual(q.text, 'hello')

    def test_parser_update(self):
        uid = 2
        self.assertTrue(MainDB.add_user(uid))
        self.assertTrue(MainDB.add_note(uid, 'hello'))

        self.assertEqual(parser.parse_note_and_update(uid, 'world', 1), 'Updated.')

        q = MainDB.get_user_note(uid, 1)
        self.assertIsNotNone(q)
        self.assertEqual(q.text, 'world')


class TestParserWithMainDBExceptions(MainDBTemplate):
    def test_parser_insert_exception(self):
        uid = 3
        self.assertTrue(MainDB.add_user(uid))

        self.assertEqual(
            parser.parse_note_and_insert(uid, bool),
            'Error: check text format and try again.'
        )

    def test_parser_update_exception(self):
        uid = 4
        self.assertTrue(MainDB.add_user(uid))
        self.assertTrue(MainDB.add_note(uid, 'hello'))

        self.assertEqual(
            parser.parse_note_and_update(uid, bool, 1),
            'Error: wrong note number or text format; check for errors and try again.'
        )
