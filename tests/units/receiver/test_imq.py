""" python -m unittest tests.units.receiver.test_imq """
import unittest

from lucky_bot.receiver import InputQueue


class TestReceiverMessageQueue(unittest.TestCase):
    def setUp(self):
        InputQueue.set_up()

    def tearDown(self):
        InputQueue.tear_down()

    def test_output_queue_works(self):
        InputQueue.add_message('foo', 1)
        InputQueue.add_message('bar', 2)
        InputQueue.add_message('baz', 3)

        for message in ['foo', 'bar', 'baz']:
            msg_obj = InputQueue.get_first_message()
            self.assertIsNotNone(msg_obj, msg=message)
            self.assertEqual(msg_obj.data, message)
            InputQueue.delete_message(msg_obj)

        result = InputQueue.get_first_message()
        self.assertIsNone(result)
