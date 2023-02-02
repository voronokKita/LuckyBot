""" python -m unittest tests.units.receiver.test_imq """
import unittest

from lucky_bot.receiver import InputQueue


class TestReceiverMessageQueue(unittest.TestCase):
    def setUp(self):
        InputQueue.set_up()

    def tearDown(self):
        InputQueue.tear_down()

    def test_output_queue_works(self):
        self.assertFalse(InputQueue.delete_message(42))
        self.assertIsNone(InputQueue.get_first_message())

        msg1 = 'foo'
        msg2 = '/delete 42'
        msg3 = '''{"id":999,"first_name":"John","last_name":"Doe","username":"john_doe"}'''

        self.assertTrue(InputQueue.add_message(msg1, time=1))
        self.assertTrue(InputQueue.add_message(msg2, time=2))
        self.assertTrue(InputQueue.add_message(msg3, time=3))

        for message in [msg1, msg2, msg3]:
            result = InputQueue.get_first_message()
            self.assertIsNotNone(result, msg=message)

            id_, text = result
            self.assertEqual(text, message)
            self.assertTrue(InputQueue.delete_message(id_))

        self.assertIsNone(InputQueue.get_first_message())
