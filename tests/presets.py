import unittest

from lucky_bot.helpers.signals import EXIT_SIGNAL, NEW_MESSAGE_TO_SEND, INCOMING_MESSAGE
from lucky_bot.helpers.constants import TestException
from lucky_bot import MainDB


class ThreadTestTemplate(unittest.TestCase):
    ''' Base tests for any thread. '''
    thread_class = None
    is_running_signal = None
    is_stopped_signal = None
    other_signals = []

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            self.thread_obj.merge()
        self._clear_signals()
        self.assertFalse(self.thread_obj.is_alive())

    def _clear_signals(self):
        signals = [EXIT_SIGNAL, self.is_running_signal, self.is_stopped_signal]
        if self.other_signals:
            signals += self.other_signals
        [signal.clear() for signal in signals if signal.is_set()]

    def normal_case(self):
        self.thread_obj.start()

        if not self.is_running_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        EXIT_SIGNAL.set()
        if str(self.thread_obj) == 'sender thread':
            NEW_MESSAGE_TO_SEND.set()
        elif str(self.thread_obj) == 'controller thread':
            INCOMING_MESSAGE.set()

        if not self.is_stopped_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to stop the {self.thread_obj} has passed.')

        self.assertFalse(self.thread_obj.is_alive())
        self.thread_obj.merge()

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
        self.assertFalse(self.thread_obj.is_alive())
        self.assertRaises(Exception, self.thread_obj.merge)

    def forced_merge(self, *args):
        self.thread_obj.start()
        if not self.is_running_signal.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the sender has passed.')

        self.thread_obj.merge()
        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(self.thread_obj.is_alive())


class ThreadSmallTestTemplate(unittest.TestCase):
    ''' Small preset for thread testing. '''
    thread_class = None
    is_running_signal = None
    is_stopped_signal = None
    other_signals = []

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            self.thread_obj.merge()
        self._clear_signals()
        self.assertFalse(self.thread_obj.is_alive())

    def _clear_signals(self):
        signals = [EXIT_SIGNAL, self.is_running_signal, self.is_stopped_signal]
        if self.other_signals:
            signals += self.other_signals
        [signal.clear() for signal in signals if signal.is_set()]


class MainDBTemplate(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()

    def tearDown(self):
        MainDB.tear_down()
