""" python -m unittest tests.units.sender.test_omq """
import unittest

from lucky_bot.sender import OutputQueue


class TestSenderMessageQueue(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()

    def tearDown(self):
        OutputQueue.tear_down()

    def test_output_queue_works(self):
        self.assertFalse(OutputQueue.delete_message(42))
        self.assertIsNone(OutputQueue.get_first_message())

        uid1 = '6'
        msg1 = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, ' \
               'sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
        uid2 = '9'
        msg2 = '/delete 999'
        uid3 = '42'
        msg3 = '{"id":42,"first_name":"John","last_name":"Doe","username":"john_doe"}'

        self.assertTrue(OutputQueue.add_message(uid1, msg1, time=1))
        self.assertTrue(OutputQueue.add_message(uid2, msg2, time=2))
        self.assertTrue(OutputQueue.add_message(uid3, msg3, time=3))

        for user, message in [(uid1, msg1), (uid2, msg2), (uid3, msg3)]:
            result = OutputQueue.get_first_message()
            self.assertIsNotNone(result, msg=user)

            message_id, uid, text, markup = result

            self.assertEqual(user, uid)
            self.assertEqual(text, message)
            self.assertFalse(markup)

            self.assertTrue(OutputQueue.delete_message(message_id))

        self.assertIsNone(OutputQueue.get_first_message())
