"""
This test should not be run together with others.
This test must be run by hands.
python tests/test_networking.py
"""
import sys

if __name__ != '__main__':
    print('Run test_networking.py as main.')
    sys.exit(1)

import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from lucky_bot.helpers.constants import TestException
from lucky_bot.helpers.signals import (
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
    RECEIVER_IS_RUNNING, CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
)
from lucky_bot.receiver import InputQueue
from lucky_bot.sender import OutputQueue
from lucky_bot import MainDB
from main import MainAsThread


class TestMain(unittest.TestCase):
    def setUp(self):
        InputQueue.set_up()
        OutputQueue.set_up()
        MainDB.set_up()
        self.main_thread = MainAsThread()

    def tearDown(self):
        if self.main_thread.is_alive():
            self.main_thread.merge()
        self.assertFalse(self.main_thread.is_alive())
        MainDB.tear_down()
        OutputQueue.tear_down()
        InputQueue.tear_down()

    def test_networking(self, *args):
        self.main_thread.start()

        signals = [
            {'name': 'sender', 'signal': SENDER_IS_RUNNING},
            {'name': 'updater', 'signal': UPDATER_IS_RUNNING},
            {'name': 'controller', 'signal': CONTROLLER_IS_RUNNING},
            {'name': 'receiver', 'signal': RECEIVER_IS_RUNNING},
            {'name': 'all threads are go', 'signal': ALL_THREADS_ARE_GO},
        ]
        for stage in signals:
            if stage['signal'].wait(10):
                if stage['name'] == 'all threads are go':
                    print('\nall threads are go signal')
            else:
                raise TestException(f'Stage Timeout: {stage["name"]}')

        if EXIT_SIGNAL.wait():
            print('exit signal')
            pass

        if not ALL_DONE_SIGNAL.wait(10):
            raise TestException('Timeout: all_done signal not called.')

        self.main_thread.merge()


if __name__ == '__main__':
    unittest.main(verbosity=2)
