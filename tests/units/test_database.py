""" python -m unittest tests.units.test_database """
import unittest

from lucky_bot.models.database import MainDB


class TestMainDatabase(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()

    def tearDown(self):
        MainDB.tear_down()

    def test_new_user(self):
        self.assertIsNone(MainDB.get_user(123))

        self.assertTrue(MainDB.add_user(123))
        self.assertFalse(MainDB.add_user(123))

        user = MainDB.get_user(123)
        self.assertIsNotNone(user)
        self.assertEqual(user.last_note, 0)

    def test_new_note(self):
        self.assertIsNone(MainDB.get_user_notes(42))

        self.assertTrue(MainDB.add_user(42))
        self.assertTrue(MainDB.add_note(42, 'hello'))

        user = MainDB.get_user(42)
        self.assertIsNotNone(user, msg='first case')
        self.assertEqual(user.last_note, 1, msg='first case')

        self.assertTrue(MainDB.add_note(9, 'genius'))
        user = MainDB.get_user(9)
        self.assertIsNotNone(user, msg='second case')
        self.assertEqual(user.last_note, 1, msg='second case')

        notes = MainDB.get_user_notes(9)
        self.assertIsNotNone(notes)
        self.assertEqual(notes[0].text, 'genius')
        self.assertEqual(notes[0].number, 1)
        self.assertIsNotNone(notes[0].date)
