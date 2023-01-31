""" python -m unittest tests.units.updater.test_update_dispatcher """
import unittest
from unittest.mock import Mock, patch
from time import time

from lucky_bot.updater import update_dispatcher


@patch('lucky_bot.updater.update_dispatcher.OutputQueue')
@patch('lucky_bot.updater.update_dispatcher.MainDB')
class TestUpdateDispatcher(unittest.TestCase):
    def setUp(self):
        self.current_time = Mock()
        self.current_time.before_the_first_update = False
        self.current_time.first_update = False
        self.current_time.second_update = False

    def test_clear_all_flags(self, db, arg):
        update_dispatcher.clear_all_users_flags(self.current_time)
        db.clear_all_users_flags.assert_not_called()

        self.current_time.before_the_first_update = True
        update_dispatcher.clear_all_users_flags(self.current_time)
        db.clear_all_users_flags.assert_called_once()

    def test_set_up_flag(self, db, arg):
        uid = 22
        update_dispatcher.set_update_flag(uid, self.current_time)
        db.set_user_flag.assert_not_called()

        self.current_time.first_update = True
        update_dispatcher.set_update_flag(uid, self.current_time)
        db.set_user_flag.assert_called_once_with(uid, 'first update')

        self.current_time.first_update = False
        self.current_time.second_update = True
        update_dispatcher.set_update_flag(uid, self.current_time)
        self.assertEqual(db.set_user_flag.call_count, 2)
        db.set_user_flag.assert_called_with(uid, 'second update')

    def test_is_waiting_for_update(self, *args):
        user = Mock()
        user.got_first_update = False
        user.got_second_update = False
        self.assertFalse(update_dispatcher.is_waiting_for_update(user, self.current_time))

        self.current_time.first_update = True
        self.assertTrue(update_dispatcher.is_waiting_for_update(user, self.current_time))

        user.got_first_update = True
        self.current_time.first_update = False
        self.current_time.second_update = True
        self.assertTrue(update_dispatcher.is_waiting_for_update(user, self.current_time))

        user.got_first_update = True
        user.got_second_update = True
        self.current_time.first_update = False
        self.current_time.second_update = False
        self.assertFalse(update_dispatcher.is_waiting_for_update(user, self.current_time))

    @patch('lucky_bot.updater.update_dispatcher.is_waiting_for_update')
    def test_messaging_without_users(self, func, db, arg):
        db.get_users_with_notes.return_value = None
        update_dispatcher.notifications_dispatcher(self.current_time)
        func.assert_not_called()

    def test_dispatcher_first_update(self, db, omq):
        user = Mock()
        user.tg_id = 1
        user.got_first_update = False
        self.current_time.first_update = True
        db.get_users_with_notes.return_value = [user]

        note = Mock()
        note.text = 'foo'
        note.number = 1
        db.get_notifications_for_the_updater.return_value = [note]

        t = int(time())
        update_dispatcher.notifications_dispatcher(self.current_time)

        db.get_users_with_notes.assert_called_once()
        db.get_notifications_for_the_updater.assert_called_once_with(user.tg_id)
        omq.add_message.assert_called_once_with(user.tg_id, note.text)
        db.update_user_last_notes_list.assert_called_once_with(user.tg_id, note.number)
        db.set_user_flag.assert_called_once_with(user.tg_id, 'first update')

    def test_dispatcher_second_update(self, db, omq):
        user = Mock()
        user.tg_id = 2
        user.got_first_update = True
        user.got_second_update = False
        self.current_time.second_update = True
        db.get_users_with_notes.return_value = [user]

        note = Mock()
        note.text = 'bar'
        note.number = 1
        db.get_notifications_for_the_updater.return_value = [note]

        t = int(time())
        update_dispatcher.notifications_dispatcher(self.current_time)

        db.get_users_with_notes.assert_called_once()
        db.get_notifications_for_the_updater.assert_called_once_with(user.tg_id)
        omq.add_message.assert_called_once_with(user.tg_id, note.text)
        db.update_user_last_notes_list.assert_called_once_with(user.tg_id, note.number)
        db.set_user_flag.assert_called_once_with(user.tg_id, 'second update')

    @patch('lucky_bot.updater.update_dispatcher.set_update_flag')
    @patch('lucky_bot.updater.update_dispatcher.is_waiting_for_update')
    def test_dispatcher_user_without_notes_error(self, is_waiting, set_flag, db, omq):
        is_waiting.return_value = True
        user = Mock()
        user.tg_id = 3
        db.get_users_with_notes.return_value = [user]
        db.get_notifications_for_the_updater.return_value = None

        update_dispatcher.notifications_dispatcher(self.current_time)

        db.get_users_with_notes.assert_called_once()
        is_waiting.assert_called_once_with(user, self.current_time)
        db.get_notifications_for_the_updater.assert_called_once_with(user.tg_id)

        omq.add_message.assert_not_called()
        set_flag.assert_not_called()
