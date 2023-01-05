import unittest

from lucky_bot.helpers.signals import EXIT_SIGNAL, NEW_MESSAGE_TO_SEND
from lucky_bot.helpers.constants import TestException


class ThreadTestTemplate(unittest.TestCase):
    ''' Base tests for any thread. '''
    thread_class = None
    is_running_signal = None
    is_stopped_signal = None
    signals = []

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            EXIT_SIGNAL.set()
            self.thread_obj.join(5)
        self._clear_signals()

    def _clear_signals(self):
        signals = [EXIT_SIGNAL, NEW_MESSAGE_TO_SEND,
                   self.is_running_signal, self.is_stopped_signal]
        if self.signals:
            signals += self.signals
        [signal.clear() for signal in signals if signal.is_set()]

    def normal_case(self):
        self.thread_obj.start()

        if not self.is_running_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        EXIT_SIGNAL.set()
        if str(self.thread_obj) == 'sender thread':
            NEW_MESSAGE_TO_SEND.set()
        if not self.is_stopped_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.thread_obj.merge()
        self.assertFalse(self.thread_obj.is_alive())

    def exception_case(self, test_exception):
        test_exception.side_effect = TestException('boom')
        self.thread_obj.start()

        if not self.is_running_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        if not self.is_stopped_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(Exception, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())
