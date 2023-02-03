""" python -m unittest tests.units.controller.test_responder """
import unittest
from unittest.mock import patch, Mock

from lucky_bot.helpers.constants import DatabaseException
from lucky_bot.helpers.misc import encrypt
from lucky_bot.helpers.signals import NEW_MESSAGE_TO_SEND
from lucky_bot.controller import Respond


@patch('lucky_bot.controller.responder.MainDB')
@patch('lucky_bot.controller.responder.OutputQueue')
class TestResponder(unittest.TestCase):
    def setUp(self):
        self.responder = Respond()

    def tearDown(self):
        if NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.clear()

    def test_responder_send_message(self, output, *args):
        uid = 1
        text = 'hello'
        self.responder.send_message(uid, text)

        output.add_message.assert_called_once_with(uid, text)
        self.assertTrue(NEW_MESSAGE_TO_SEND.is_set())

    def test_responder_delete_user(self, arg, db):
        uid = 2
        self.responder.delete_user(uid, start_cmd=True)
        db.delete_user.assert_called_once_with(uid)

    def test_responder_delete_notes(self, output, db):
        uid = 3
        self.responder.delete_notes(uid, [1, 2, 3])

        self.assertEqual(db.delete_user_note.call_count, 3)
        output.add_message.assert_called_once()

        expected = "Note #`1` - deleted\n" \
                   "Note #`2` - deleted\n" \
                   "Note #`3` - deleted\n"
        result = output.add_message.call_args.args
        self.assertEqual(result[1], expected)

    def test_responder_delete_notes_wrong(self, output, db):
        uid = 3
        db.delete_user_note.return_value = False
        self.responder.delete_notes(uid, [1])

        db.delete_user_note.assert_called_once()
        output.add_message.assert_called_once()

        result = output.add_message.call_args.args
        self.assertEqual(result[1], 'Note #`1` - not found\n')

    def test_responder_delete_notes_exception(self, output, db):
        uid = 3
        db.delete_user_note.side_effect = [False, True, DatabaseException('boom')]
        self.assertRaises(DatabaseException, self.responder.delete_notes, uid, [1, 2, 3])

        self.assertEqual(db.delete_user_note.call_count, 3)
        output.add_message.assert_called_once()

        expected = "Note #`1` - not found\n" \
                   "Note #`2` - deleted\n" \
                   "Some internal Error...\n"
        result = output.add_message.call_args.args
        self.assertEqual(result[1], expected)

    def test_responder_send_list(self, output, db):
        uid = 4
        note = Mock()
        text = 'foo, bar, baz, qux, quux, corge, grault, garply, waldo, fred, plugh, xyzzy, thud'
        note.number = 1
        expecting = f'Your notes:\n* №`{note.number}` :: "{text[:30]}..."\n\n'
        note.text = encrypt(text)
        db.get_user_notes.return_value = [note]

        self.responder.send_list(uid)

        db.get_user_notes.assert_called_once()
        output.add_message.assert_called_once()

        result = output.add_message.call_args.args
        self.assertEqual(result[1], expecting)

    def test_responder_send_list_empty(self, output, db):
        db.get_user_notes.return_value = None
        self.responder.send_list(4)

        output.add_message.assert_called_once()
        result = output.add_message.call_args.args
        self.assertEqual(result[1], 'Nothing.')

    def test_responder_send_note(self, output, db):
        uid = 5
        note_num = 1
        note = Mock()
        note.text = encrypt('foobar')
        db.get_user_note.return_value = note

        self.responder.send_note(uid, note_num)

        db.get_user_note.assert_called_once()

        output.add_message.assert_called_once()
        result = output.add_message.call_args.args
        self.assertIsInstance(result[0], bytes)
        self.assertEqual(result[1], note.text)

    def test_responder_send_note_wrong(self, output, db):
        uid = 5
        db.get_user_note.return_value = None
        self.responder.send_note(uid, 1)

        output.add_message.assert_called_once()
        result = output.add_message.call_args.args
        self.assertEqual(result[1], 'Number not found. Check the note number by calling /list.')
