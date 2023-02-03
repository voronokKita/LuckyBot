""" python -m unittest tests.integration.controller.test_responder_integration """
import unittest

from lucky_bot.helpers.signals import NEW_MESSAGE_TO_SEND
from lucky_bot import MainDB
from lucky_bot.sender import OutputQueue
from lucky_bot.controller import Respond


class TestResponderIntegration(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()
        OutputQueue.set_up()
        self.respond = Respond()

    def tearDown(self):
        MainDB.tear_down()
        OutputQueue.tear_down()
        if NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.clear()

    def test_responder_send_message(self):
        uid = '1'
        text = 'hello'
        self.respond.send_message(uid, text)

        self.assertTrue(NEW_MESSAGE_TO_SEND.is_set())

        result = OutputQueue.get_first_message()
        self.assertIsNotNone(result)
        msg_id, msg_uid, msg_text, markup = result
        self.assertEqual(msg_uid, uid)
        self.assertEqual(msg_text, text)

    def test_responder_delete_user(self):
        uid = '2'
        self.assertTrue(MainDB.add_user(uid))
        self.respond.delete_user(uid, True)
        self.assertIsNone(MainDB.get_user(uid))

    def test_responder_delete_notes(self):
        uid = '3'
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'foo')
        MainDB.add_note(uid, 'bar')
        MainDB.add_note(uid, 'baz')

        self.respond.delete_notes(uid, [1, 2, 3])

        self.assertEqual(MainDB.get_user_notes(uid), [])
        expected = "Note #1 - deleted\n" \
                   "Note #2 - deleted\n" \
                   "Note #3 - deleted\n"
        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        self.assertEqual(msg_text, expected)

    def test_responder_delete_notes_wrong(self):
        uid = '3'
        MainDB.add_user(uid)
        self.respond.delete_notes(uid, [1])

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        self.assertEqual(msg_text, f'Note #1 - not found\n')

    def test_responder_send_list(self):
        uid = '4'
        note_text = 'foo, bar, baz, qux, quux, corge, grault, garply, waldo, fred, plugh, xyzzy, thud'

        lines = note_text[:40].splitlines()
        text1 = '_'.join([l for l in lines if l])
        text2 = text1[:30].strip()

        MainDB.add_user(uid)
        MainDB.add_note(uid, note_text)

        self.respond.send_list(uid)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        expecting = f'Your notes:\n* №1 :: "{text2[:30]}..."\n\n'
        self.assertEqual(msg_text, expecting)

    def test_responder_send_list_empty(self):
        uid = '4'
        MainDB.add_user(uid)

        self.respond.send_list(uid)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        self.assertEqual(msg_text, 'Nothing.')

    def test_responder_send_note(self):
        uid = '5'
        note_text = 'foobar'
        MainDB.add_user(uid)
        MainDB.add_note(uid, note_text)

        self.respond.send_note(uid, note_num=1)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        self.assertEqual(msg_text, note_text)

    def test_responder_send_note_wrong(self):
        uid = '5'
        MainDB.add_user(uid)

        self.respond.send_note(uid, note_num=1)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        msg_id, msg_uid, msg_text, markup = msg
        expecting = 'Number not found. Check the note number by calling /list.'
        self.assertEqual(msg_text, expecting)
