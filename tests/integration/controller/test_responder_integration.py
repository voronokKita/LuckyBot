""" python -m unittest tests.integration.controller.test_responder_integration """
import time
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
        uid = 1
        t = int(time.time())
        self.respond.send_message(uid, 'hello')

        self.assertTrue(NEW_MESSAGE_TO_SEND.is_set())

        result = OutputQueue.get_first_message()
        self.assertIsNotNone(result)
        self.assertEqual(result.destination, uid)
        self.assertEqual(result.text, 'hello')
        self.assertGreaterEqual(result.time, t)

    def test_responder_delete_user(self):
        uid = 2
        self.assertTrue(MainDB.add_user(uid))

        self.respond.delete_user(uid, True)

        self.assertIsNone(MainDB.get_user(uid))

    def test_responder_delete_notes(self):
        uid = 3
        MainDB.add_user(uid)
        MainDB.add_note(uid, 'foo')
        MainDB.add_note(uid, 'bar')
        MainDB.add_note(uid, 'baz')

        self.respond.delete_notes(uid, [1, 2, 3])

        self.assertEqual(MainDB.get_user_notes(uid), [])
        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, 'Deleted.')

    def test_responder_delete_notes_wrong(self):
        uid = 3
        MainDB.add_user(uid)
        self.respond.delete_notes(uid, [1])

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, f'Note #1 - fail to delete.\n')

    def test_responder_send_list(self):
        note_text = 'foo, bar, baz, qux, quux, corge, grault, garply, waldo, fred, plugh, xyzzy, thud'
        expecting = f'Your notes:\n* №1 :: "{note_text[:30]}..."\n\n'
        uid = 4
        MainDB.add_user(uid)
        MainDB.add_note(uid, note_text)

        self.respond.send_list(uid)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, expecting)

    def test_responder_send_list_empty(self):
        uid = 4
        MainDB.add_user(uid)

        self.respond.send_list(uid)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, 'Nothing.')

    def test_responder_send_note(self):
        note_text = 'foobar'
        uid = 5
        MainDB.add_user(uid)
        MainDB.add_note(uid, note_text)

        self.respond.send_note(uid, 1)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.text, note_text)

    def test_responder_send_note_wrong(self):
        uid = 5
        MainDB.add_user(uid)

        self.respond.send_note(uid, 1)

        msg = OutputQueue.get_first_message()
        self.assertIsNotNone(msg)
        expecting = 'Number not found. Check the note number by calling /list.'
        self.assertEqual(msg.text, expecting)
