""" Updater.

A module that handles the distribution of messages to the users on a schedule.
"""
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


class UpdaterThread(ThreadTemplate):
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def __str__(self):
        return 'updater thread'

    def body(self):
        self._set_the_signal()
        self._test_exception_after_signal()
        if EXIT_SIGNAL.wait():
            pass
