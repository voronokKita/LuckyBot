""" python -m unittest tests.units.test_database """
import unittest

from lucky_bot.database import MainDB


class TestMainDatabase(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()

    def tearDown(self):
        MainDB.tear_down()

    def test_db_new_user(self):
        uid = 123
        self.assertIsNone(MainDB.get_user(uid))

        self.assertTrue(MainDB.add_user(uid))
        self.assertFalse(MainDB.add_user(uid))

        user = MainDB.get_user(uid)
        self.assertIsNotNone(user)
        self.assertEqual(user.last_note, 0)

    def test_db_new_note(self):
        uid1 = 42
        self.assertIsNone(MainDB.get_user_notes(uid1))

        self.assertTrue(MainDB.add_user(uid1))
        self.assertTrue(MainDB.add_note(uid1, 'hello'))

        user1 = MainDB.get_user(uid1)
        self.assertIsNotNone(user1, msg='first case')
        self.assertEqual(user1.last_note, 1, msg='first case')

        uid2 = 9
        self.assertTrue(MainDB.add_note(uid2, 'strongest'))
        self.assertTrue(MainDB.add_note(uid2, 'genius'))
        user2 = MainDB.get_user(uid2)
        self.assertIsNotNone(user2, msg='second case')
        self.assertEqual(user2.last_note, 2, msg='second case')

        notes = MainDB.get_user_notes(uid2)
        self.assertIsNotNone(notes)
        self.assertEqual(notes[0].text, 'strongest')
        self.assertEqual(notes[1].text, 'genius')
        self.assertEqual(notes[0].number, 1)
        self.assertEqual(notes[1].number, 2)
        self.assertIsNotNone(notes[0].date)
        self.assertIsNotNone(notes[1].date)

    def test_db_delete_note(self):
        uid = 20
        self.assertIsNone(MainDB.get_user(uid))
        self.assertFalse(MainDB.delete_user_note(uid, note_num=0), msg='1')
        self.assertFalse(MainDB.delete_user_note(uid, note_num=1), msg='1')

        # test two entries
        self.assertTrue(MainDB.add_note(uid, 'hello'), msg='1')
        self.assertTrue(MainDB.add_note(uid, 'world'), msg='1')

        user_1 = MainDB.get_user(uid)
        self.assertIsNotNone(user_1, msg='1')
        self.assertEqual(user_1.last_note, 2, msg='1')

        notes_1 = MainDB.get_user_notes(uid)
        self.assertIsNotNone(notes_1, msg='1')
        self.assertEqual(len(notes_1), 2, msg='1')
        self.assertEqual(notes_1[0].text, 'hello', msg='1')
        self.assertEqual(notes_1[1].text, 'world', msg='1')
        self.assertEqual(notes_1[0].number, 1, msg='1')
        self.assertEqual(notes_1[1].number, 2, msg='1')

        # delete 1st entry
        self.assertFalse(MainDB.delete_user_note(uid, note_num=0), msg='2')
        self.assertTrue(MainDB.delete_user_note(uid, note_num=1), msg='2')

        # user still has the greatest number in "last_note"
        user_2 = MainDB.get_user(uid)
        self.assertEqual(user_2.last_note, 2, msg='2')

        # the last note still has the greatest number
        notes_2 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_2), 1, msg='2')
        self.assertEqual(notes_2[0].text, 'world', msg='2')
        self.assertEqual(notes_2[0].number, 2, msg='2')

        # add a 3rd entry
        self.assertTrue(MainDB.add_note(uid, 'foobar'), msg='3')

        user_3 = MainDB.get_user(uid)
        self.assertEqual(user_3.last_note, 3, msg='3')

        notes_3 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_3), 2, msg='3')
        self.assertEqual(notes_3[0].text, 'world', msg='3')
        self.assertEqual(notes_3[1].text, 'foobar', msg='3')
        self.assertEqual(notes_3[0].number, 2, msg='3')
        self.assertEqual(notes_3[1].number, 3, msg='3')

        # delete the 3rd entry and add a 4th
        self.assertTrue(MainDB.delete_user_note(uid, note_num=3), msg='4')
        self.assertTrue(MainDB.add_note(uid, 'bazqux'), msg='4')

        user_4 = MainDB.get_user(uid)
        self.assertEqual(user_4.last_note, 4, msg='4')

        notes_4 = MainDB.get_user_notes(uid)
        self.assertEqual(notes_4[0].text, 'world', msg='4')
        self.assertEqual(notes_4[1].text, 'bazqux', msg='4')
        self.assertEqual(notes_4[0].number, 2, msg='4')
        self.assertEqual(notes_4[1].number, 4, msg='4')

    def test_db_delete_user(self):
        uid1 = 404
        uid2 = 200
        self.assertFalse(MainDB.delete_user(uid1), msg='first')

        self.assertTrue(MainDB.add_user(uid1))
        self.assertTrue(MainDB.add_note(uid1, 'uid-1 note-1'))
        self.assertTrue(MainDB.add_note(uid1, 'uid-1 note-2'))
        self.assertTrue(MainDB.add_user(uid2))
        self.assertTrue(MainDB.add_note(uid2, 'uid-2 note-1'))

        user1 = MainDB.get_user(uid1)
        self.assertIsNotNone(user1)
        self.assertEqual(user1.last_note, 2)
        notes1 = MainDB.get_user_notes(uid1)
        self.assertIsNotNone(notes1)
        self.assertEqual(len(notes1), 2)

        self.assertTrue(MainDB.delete_user(uid1), msg='second')
        user1 = MainDB.get_user(uid1)
        self.assertIsNone(user1)
        notes1 = MainDB.get_user_notes(uid1)
        self.assertIsNone(notes1)

        # assert 2nd user do not connected in any way
        self.assertTrue(MainDB.add_note(uid2, 'uid-2 note-2'))
        user2 = MainDB.get_user(uid2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.last_note, 2)
        notes2 = MainDB.get_user_notes(uid2)
        self.assertIsNotNone(notes2)
        self.assertEqual(len(notes2), 2)
        self.assertEqual(notes2[0].text, 'uid-2 note-1')
        self.assertEqual(notes2[1].text, 'uid-2 note-2')
        self.assertEqual(notes2[0].number, 1)
        self.assertEqual(notes2[1].number, 2)

    def test_db_update_note(self):
        uid = 300
        self.assertFalse(MainDB.update_user_note(uid, 0, 'null'), msg='first')
        self.assertFalse(MainDB.update_user_note(uid, 1, 'null'), msg='first')

        self.assertTrue(MainDB.add_note(uid, 'foo'))
        self.assertTrue(MainDB.add_note(uid, 'bar'))

        user_1 = MainDB.get_user(uid)
        self.assertIsNotNone(user_1)
        self.assertEqual(user_1.last_note, 2)
        notes_1 = MainDB.get_user_notes(uid)
        self.assertIsNotNone(notes_1)
        self.assertEqual(len(notes_1), 2)
        self.assertEqual(notes_1[0].text, 'foo')
        self.assertEqual(notes_1[1].text, 'bar')
        self.assertEqual(notes_1[0].number, 1)
        self.assertEqual(notes_1[1].number, 2)

        self.assertFalse(MainDB.update_user_note(uid, 0, 'null'), msg='second')
        self.assertTrue(MainDB.update_user_note(uid, 1, 'baz'), msg='second')

        user_2 = MainDB.get_user(uid)
        self.assertEqual(user_2.last_note, 2)
        notes_2 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_2), 2)
        self.assertEqual(notes_2[0].text, 'baz')
        self.assertEqual(notes_2[1].text, 'bar')
        self.assertEqual(notes_2[0].number, 1)
        self.assertEqual(notes_2[1].number, 2)
