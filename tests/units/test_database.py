""" python -m unittest tests.units.test_database """
from unittest.mock import patch

from lucky_bot.helpers.constants import TestException, DatabaseException
from lucky_bot.helpers.misc import decrypt, make_hash
from lucky_bot import MainDB

from tests.presets import MainDBTemplate


class TestMainDatabase(MainDBTemplate):
    def test_add_get_and_delete_user(self):
        self.assertIsNone(MainDB.get_user(42), msg="user don't exist")
        self.assertFalse(MainDB.delete_user(42), msg="user don't exist")

        uid = '1'
        self.assertTrue(MainDB.add_user(uid))
        self.assertFalse(MainDB.add_user(uid), msg='user already exists')

        user = MainDB.get_user(uid)
        self.assertIsNotNone(user)

        self.assertTrue(MainDB.delete_user(uid))
        self.assertIsNone(MainDB.get_user(uid))

    def test_add_get_update_and_delete_note(self):
        self.assertFalse(MainDB.add_note(42, 'foo'), msg="user don't exist")
        self.assertIsNone(MainDB.get_user_note(42, 1), msg="user don't exist")
        self.assertFalse(MainDB.update_user_note(42, 1, 'bar'), msg="user don't exist")
        self.assertFalse(MainDB.delete_user_note('hash-42', 1), msg="user don't exist")

        uid = '2'
        uid_hash = make_hash(uid)
        MainDB.add_user(uid)
        note_num = 1
        self.assertIsNone(MainDB.get_user_note(uid, note_num), msg="note don't exist")
        self.assertFalse(MainDB.update_user_note(uid, note_num, 'bar'), msg="note don't exist")
        self.assertFalse(MainDB.delete_user_note(uid_hash, note_num), msg="note don't exist")

        note_text = 'hello'
        self.assertTrue(MainDB.add_note(uid, note_text))

        note_q1 = MainDB.get_user_note(uid, note_num)
        self.assertIsNotNone(note_q1)
        self.assertEqual(decrypt(note_q1.text), note_text)

        new_note_text = 'world'
        self.assertTrue(MainDB.update_user_note(uid, note_num, new_note_text))
        note_q2 = MainDB.get_user_note(uid, note_num)
        self.assertEqual(decrypt(note_q2.text), new_note_text)

        self.assertTrue(MainDB.delete_user_note(uid_hash, note_num))
        self.assertIsNone(MainDB.get_user_note(uid, note_num))

    def test_get_users_and_notes_lists(self):
        self.assertEqual(MainDB.get_user_notes(42), [], msg="user don't exist")
        self.assertEqual(MainDB.get_users_with_notes(), [], msg="no user exists")

        uid1 = '3'
        uid2 = '4'
        MainDB.add_user(uid1)
        MainDB.add_user(uid2)
        self.assertEqual(MainDB.get_user_notes(uid1), [], msg="user don't have any notes")
        self.assertEqual(MainDB.get_users_with_notes(), [], msg="no user with notes")

        note_one_text = 'hello'
        note_two_text = 'world'
        MainDB.add_note(uid1, note_one_text)
        MainDB.add_note(uid1, note_two_text)

        notes = MainDB.get_user_notes(uid1)
        self.assertEqual(len(notes), 2)

        users = MainDB.get_users_with_notes()
        self.assertEqual(len(users), 1)
        self.assertEqual(decrypt(users[0].c_id), uid1)

    @patch('lucky_bot.database.test_func')
    def test_database_exception(self, func):
        func.side_effect = TestException('boom')
        self.assertRaises(DatabaseException, MainDB.add_user, 42)


class TestMainDatabaseDeeper(MainDBTemplate):
    def test_db_user(self):
        uid = '123'
        MainDB.add_user(uid)

        user = MainDB.get_user(uid)
        self.assertEqual(user.last_note, 0)
        self.assertEqual(user.notes_total, 0)
        self.assertEqual(user.got_first_update, False)
        self.assertEqual(user.got_second_update, False)
        self.assertEqual(decrypt(user.c_id), uid)

    def test_db_add_and_get_notes(self):
        # first user
        uid1 = '321'
        MainDB.add_user(uid1)
        MainDB.add_note(uid1, 'hello')

        user1 = MainDB.get_user(uid1)
        self.assertEqual(user1.last_note, 1)
        self.assertEqual(user1.notes_total, 1)

        # second user
        uid2 = '9'
        MainDB.add_user(uid2)
        MainDB.add_note(uid2, 'strongest')
        MainDB.add_note(uid2, 'genius')

        user2 = MainDB.get_user(uid2)
        self.assertEqual(user2.last_note, 2)
        self.assertEqual(user2.notes_total, 2)

        u2_notes = MainDB.get_user_notes(uid2)
        self.assertEqual(decrypt(u2_notes[0].text), 'strongest')
        self.assertEqual(decrypt(u2_notes[1].text), 'genius')
        self.assertEqual(u2_notes[0].number, 1)
        self.assertEqual(u2_notes[1].number, 2)
        self.assertIsNotNone(u2_notes[0].date)
        self.assertIsNotNone(u2_notes[1].date)

        # get single note
        MainDB.add_note(uid2, 'smartest')
        note = MainDB.get_user_note(uid2, 3)
        self.assertEqual(decrypt(note.text), 'smartest')

    def test_db_delete_note(self):
        uid = '20'
        uid_hash = make_hash(uid)

        # test two entries
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'hello')
        MainDB.add_note(uid, 'world')

        user_q1 = MainDB.get_user(uid)
        self.assertEqual(user_q1.last_note, 2)
        self.assertEqual(user_q1.notes_total, 2)

        notes_q1 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_q1), 2)
        self.assertEqual(decrypt(notes_q1[0].text), 'hello')
        self.assertEqual(decrypt(notes_q1[1].text), 'world')
        self.assertEqual(notes_q1[0].number, 1)
        self.assertEqual(notes_q1[1].number, 2)

        # delete 1st entry
        MainDB.delete_user_note(uid_hash, 1)

        # the user still has the greatest number in "last_note"
        user_q2 = MainDB.get_user(uid)
        self.assertEqual(user_q2.last_note, 2)
        self.assertEqual(user_q2.notes_total, 1)

        # the last note still has the greatest number
        notes_q2 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_q2), 1)
        self.assertEqual(decrypt(notes_q2[0].text), 'world')
        self.assertEqual(notes_q2[0].number, 2)

        # add a 3rd entry
        MainDB.add_note(uid, 'foobar')

        user_q3 = MainDB.get_user(uid)
        self.assertEqual(user_q3.last_note, 3)
        self.assertEqual(user_q3.notes_total, 2)

        notes_q3 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_q3), 2)
        self.assertEqual(decrypt(notes_q3[0].text), 'world')
        self.assertEqual(decrypt(notes_q3[1].text), 'foobar')
        self.assertEqual(notes_q3[0].number, 2)
        self.assertEqual(notes_q3[1].number, 3)

        # delete the 3rd entry and add a 4th
        MainDB.delete_user_note(uid_hash, 3)
        MainDB.add_note(uid, 'bazqux')

        user_q4 = MainDB.get_user(uid)
        self.assertEqual(user_q4.last_note, 4)
        self.assertEqual(user_q4.notes_total, 2)

        notes_q4 = MainDB.get_user_notes(uid)
        self.assertEqual(decrypt(notes_q4[0].text), 'world')
        self.assertEqual(decrypt(notes_q4[1].text), 'bazqux')
        self.assertEqual(notes_q4[0].number, 2)
        self.assertEqual(notes_q4[1].number, 4)

    def test_db_delete_user(self):
        uid1 = '404'
        uid2 = '200'

        MainDB.add_user(uid1)
        MainDB.add_note(uid1, 'uid-1 note-1')
        MainDB.add_note(uid1, 'uid-1 note-2')
        MainDB.add_user(uid2)
        MainDB.add_note(uid2, 'uid-2 note-1')
        MainDB.add_note(uid2, 'uid-2 note-2')

        MainDB.delete_user(uid1)
        user1 = MainDB.get_user(uid1)
        self.assertIsNone(user1)
        notes1 = MainDB.get_user_notes(uid1)
        self.assertEqual(notes1, [])

        # assert 2nd user do not connected in any way
        user2 = MainDB.get_user(uid2)
        self.assertIsNotNone(user2)
        self.assertEqual(user2.last_note, 2)
        self.assertEqual(user2.notes_total, 2)

        notes2 = MainDB.get_user_notes(uid2)
        self.assertIsNotNone(notes2)
        self.assertEqual(len(notes2), 2)
        self.assertEqual(decrypt(notes2[0].text), 'uid-2 note-1')
        self.assertEqual(decrypt(notes2[1].text), 'uid-2 note-2')
        self.assertEqual(notes2[0].number, 1)
        self.assertEqual(notes2[1].number, 2)

    def test_db_update_note(self):
        uid = '300'
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'foo')
        MainDB.add_note(uid, 'bar')

        user_q1 = MainDB.get_user(uid)
        self.assertEqual(user_q1.last_note, 2)
        self.assertEqual(user_q1.notes_total, 2)

        notes_q1 = MainDB.get_user_notes(uid)
        self.assertIsNotNone(notes_q1)
        self.assertEqual(len(notes_q1), 2)
        self.assertEqual(decrypt(notes_q1[0].text), 'foo')
        self.assertEqual(decrypt(notes_q1[1].text), 'bar')
        self.assertEqual(notes_q1[0].number, 1)
        self.assertEqual(notes_q1[1].number, 2)

        self.assertFalse(MainDB.update_user_note(uid, 0, 'null'))
        self.assertTrue(MainDB.update_user_note(uid, 1, 'baz'))

        user_q2 = MainDB.get_user(uid)
        self.assertEqual(user_q2.last_note, 2)
        self.assertEqual(user_q2.notes_total, 2)

        notes_q2 = MainDB.get_user_notes(uid)
        self.assertEqual(len(notes_q2), 2)
        self.assertEqual(decrypt(notes_q2[0].text), 'baz')
        self.assertEqual(decrypt(notes_q2[1].text), 'bar')
        self.assertEqual(notes_q2[0].number, 1)
        self.assertEqual(notes_q2[1].number, 2)


@patch('lucky_bot.database.LAST_NOTES_LIST', 3)
class TestMainDatabaseUpdaterLogic(MainDBTemplate):
    def test_get_users_with_notes(self):
        self.assertEqual(MainDB.get_users_with_notes(), [])

        uid1 = '1'
        uid2 = '2'
        MainDB.add_user(uid1)
        MainDB.add_user(uid2)
        MainDB.add_note(uid1, 'foo')

        users = MainDB.get_users_with_notes()
        self.assertIsNotNone(users)
        self.assertEqual(len(users), 1)
        self.assertEqual(decrypt(users[0].c_id), uid1)

    def test_set_and_clear_user_flags(self):
        self.assertFalse(MainDB.clear_all_users_flags())

        uid1 = '31'
        uid2 = '32'
        uid1_hash = make_hash(uid1)
        uid2_hash = make_hash(uid2)
        MainDB.add_user(uid1)
        MainDB.add_user(uid2)
        MainDB.set_user_flag(uid1_hash, 'first update')
        MainDB.set_user_flag(uid1_hash, 'second update')
        MainDB.set_user_flag(uid2_hash, 'first update')
        MainDB.set_user_flag(uid2_hash, 'second update')

        user1 = MainDB.get_user(uid1)
        self.assertEqual(user1.got_first_update, True)
        self.assertEqual(user1.got_second_update, True)
        user2 = MainDB.get_user(uid2)
        self.assertEqual(user2.got_first_update, True)
        self.assertEqual(user2.got_second_update, True)

        self.assertTrue(MainDB.clear_all_users_flags())
        user1 = MainDB.get_user(uid1)
        self.assertEqual(user1.got_first_update, False)
        self.assertEqual(user1.got_second_update, False)
        user2 = MainDB.get_user(uid2)
        self.assertEqual(user2.got_first_update, False)
        self.assertEqual(user2.got_second_update, False)

    def test_updater_methods_first(self):
        """ user's notes_total list is too small to manage. """
        uid = '109'
        uid_hash = make_hash(uid)
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'one')
        MainDB.add_note(uid, 'two')
        MainDB.add_note(uid, 'three')

        notes_q1 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertIsNotNone(notes_q1)
        self.assertEqual(len(notes_q1), 3, msg='notes == user.notes')

        last_note = notes_q1[0].number
        self.assertTrue(
            MainDB.update_user_last_notes_list(uid_hash, last_note),
            msg='user.notes_total <= LAST_NOTES_LIST'
        )
        notes_q2 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q2), 3, msg='nothing has changed')
        notes_numbers = [n.number for n in notes_q2]
        self.assertIn(last_note, notes_numbers, msg='the last_note still goes to the updater')

    def test_updater_methods_second(self):
        """ user's notes_total list is bigger than the LAST_NOTES_LIST. """
        uid = '110'
        uid_hash = make_hash(uid)
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'one')
        MainDB.add_note(uid, 'two')
        MainDB.add_note(uid, 'three')
        MainDB.add_note(uid, 'four')

        notes_q1 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertIsNotNone(notes_q1)
        self.assertEqual(
            len(notes_q1), 4,
            msg='user.notes_total > LAST_NOTES_LIST and NOT user.last_notes'
        )
        last_note = notes_q1[0].number
        self.assertTrue(
            MainDB.update_user_last_notes_list(uid_hash, last_note),
            msg='user.last_notes is None'
        )
        notes_q2 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q2), 3, msg='the last_note has been filtered')
        notes_numbers = [n.number for n in notes_q2]
        self.assertNotIn(last_note, notes_numbers)

    def test_updater_methods_third(self):
        """
        user's notes_total list is bigger than the LAST_NOTES_LIST.
        Go through the full cycle.
        """
        uid = '110'
        uid_hash = make_hash(uid)
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'one')
        MainDB.add_note(uid, 'two')
        MainDB.add_note(uid, 'three')
        MainDB.add_note(uid, 'four')
        self.assertTrue(MainDB.update_user_last_notes_list(uid_hash, 1))
        self.assertTrue(MainDB.update_user_last_notes_list(uid_hash, 2))
        self.assertTrue(MainDB.update_user_last_notes_list(uid_hash, 3))

        notes_q1 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertIsNotNone(notes_q1)
        self.assertEqual(len(notes_q1), 1)
        self.assertEqual(decrypt(notes_q1[0].text), 'four')
        self.assertEqual(notes_q1[0].number, 4)

        MainDB.update_user_last_notes_list(uid_hash, notes_q1[0].number)
        notes_q2 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q2), 1)
        self.assertEqual(decrypt(notes_q2[0].text), 'one')
        self.assertEqual(notes_q2[0].number, 1)

        MainDB.update_user_last_notes_list(uid_hash, notes_q2[0].number)
        notes_q3 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q3), 1)
        self.assertEqual(decrypt(notes_q3[0].text), 'two')
        self.assertEqual(notes_q3[0].number, 2)

        MainDB.update_user_last_notes_list(uid_hash, notes_q3[0].number)
        notes_q4 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q4), 1)
        self.assertEqual(decrypt(notes_q4[0].text), 'three')
        self.assertEqual(notes_q4[0].number, 3)

        MainDB.update_user_last_notes_list(uid_hash, notes_q4[0].number)
        notes_q5 = MainDB.get_notifications_for_the_updater(None, uid_hash)
        self.assertEqual(len(notes_q5), 1)
        self.assertEqual(decrypt(notes_q5[0].text), 'four')
        self.assertEqual(notes_q5[0].number, 4)

        self.assertTrue(MainDB.update_user_last_notes_list(uid_hash, notes_q5[0].number))
