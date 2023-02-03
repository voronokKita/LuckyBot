import unittest
from unittest.mock import Mock

from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, UPDATER_IS_RUNNING,
    CONTROLLER_IS_RUNNING, RECEIVER_IS_RUNNING,

    SENDER_IS_STOPPED, UPDATER_IS_STOPPED,
    CONTROLLER_IS_STOPPED, RECEIVER_IS_STOPPED,

    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL,
    INCOMING_MESSAGE, NEW_MESSAGE_TO_SEND,
    EXIT_SIGNAL, UPDATER_CYCLE,
)
from lucky_bot.helpers.constants import TestException
from lucky_bot import MainDB

SIGNALS = [
    SENDER_IS_RUNNING, UPDATER_IS_RUNNING,
    CONTROLLER_IS_RUNNING, RECEIVER_IS_RUNNING,
    SENDER_IS_STOPPED, UPDATER_IS_STOPPED,
    CONTROLLER_IS_STOPPED, RECEIVER_IS_STOPPED,
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL,
    INCOMING_MESSAGE, NEW_MESSAGE_TO_SEND,
    EXIT_SIGNAL, UPDATER_CYCLE,
]


def mock_ngrok():
    tunnel = Mock()
    tunnel.public_url = 'http://0.0.0.0'
    ngrok = Mock()
    ngrok.connect.return_value = tunnel
    return ngrok


def mock_telebot():
    bot = Mock()
    bot.set_webhook.return_value = True
    return bot


def mock_serving():
    def start_server(self=None):
        EXIT_SIGNAL.wait()
    return start_server


class ThreadTestTemplate(unittest.TestCase):
    ''' Base tests for any thread. '''
    thread_class = None
    is_running_signal = None
    is_stopped_signal = None
    signal_after_exit = None

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            self.thread_obj.merge()
        [signal.clear() for signal in SIGNALS if signal.is_set()]
        self.assertFalse(self.thread_obj.is_alive())

    def normal_case(self):
        self.thread_obj.start()

        if not self.is_running_signal.wait(10):
            self.thread_obj.merge()
            raise TestException(f'The time to start the {self.thread_obj} has passed.')

        EXIT_SIGNAL.set()
        if self.signal_after_exit:
            self.signal_after_exit.set()

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

    def setUp(self):
        self.thread_obj = self.thread_class()

    def tearDown(self):
        if self.thread_obj.is_alive():
            self.thread_obj.merge()
        [signal.clear() for signal in SIGNALS if signal.is_set()]
        self.assertFalse(self.thread_obj.is_alive())


class MainDBTemplate(unittest.TestCase):
    def setUp(self):
        MainDB.set_up()

    def tearDown(self):
        MainDB.tear_down()
