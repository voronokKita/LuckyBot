""" python -m unittest tests.units.sender.test_omq """
import unittest

from lucky_bot.sender import OutputQueue



class TestSenderMessageQueue(unittest.TestCase):
    def setUp(self):
        OutputQueue.set_up()

    def tearDown(self):
        OutputQueue.tear_down()

    def test_output_queue_works(self):
        OutputQueue.add_message(42, 'foo', 1)
        OutputQueue.add_message(42, 'bar', 2)
        OutputQueue.add_message(42, 'baz', 3)

        for message in ['foo', 'bar', 'baz']:
            msg_obj = OutputQueue.get_first_message()
            self.assertIsNotNone(msg_obj, msg=message)
            self.assertEqual(msg_obj.text, message)
            OutputQueue.delete_message(msg_obj)

        result = OutputQueue.get_first_message()
        self.assertIsNone(result)
