import unittest

from lucky_bot.helpers.signals import EXIT_SIGNAL
from lucky_bot.helpers.constants import TestException, ThreadException

class ThreadTestTemplate(unittest.TestCase):
    thread_class = None
    is_running_signal = None
    is_stopped_signal = None
    used_signals = []

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            EXIT_SIGNAL.set()
            self.thread_obj.join(5)
        self._clear_signals()

    @classmethod
    def _clear_signals(cls):
        signals = [EXIT_SIGNAL, cls.is_running_signal, cls.is_stopped_signal]
        [signal.clear() for signal in signals if signal.is_set()]

    def normal_case(self):
        self.thread_obj.start()

        if self.is_running_signal.wait(10):
            pass
        else:
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        EXIT_SIGNAL.set()
        if self.is_stopped_signal.wait(10):
            pass
        else:
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.thread_obj.merge()
        self.assertFalse(self.thread_obj.is_alive())

    def exception_case(self, test_exception):
        test_exception.side_effect = TestException('boom')
        self.thread_obj.start()

        if self.is_running_signal.wait(10):
            pass
        else:
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        if self.is_stopped_signal.wait(10):
            pass
        else:
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertRaises(ThreadException, self.thread_obj.merge)
        self.assertFalse(self.thread_obj.is_alive())