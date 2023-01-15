""" Controller.

A module that handles incoming Telegram messages, the internal and admin commands.
Integrated with the Input Messages Queue, Parser and Responder.
"""
from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


class ControllerThread(ThreadTemplate):
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    def __str__(self):
        return 'controller thread'

    def body(self):
        self._set_the_signal()
        self._test_exception_after_signal()
        if EXIT_SIGNAL.wait():
            pass
