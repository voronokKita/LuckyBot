""" Controller thread.
Integrated with the Input Messages Queue, Parser and Responder.
"""
# from lucky_bot.helpers.constants import *
from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate

import logging
from logs import console, event
logger = logging.getLogger(__name__)


class ControllerThread(ThreadTemplate):
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    def __str__(self):
        return 'controller thread'

    def body(self):
        """
        Description:
            0. Check the Input Message Queue; respond or parse any messages;
            1. Clear NEW_INCOMING_MESSAGE, if set;
            2. Set the CONTROLLER_IS_RUNNING signal;
            3. Loop and wait for the NEW_INCOMING_MESSAGE signal.

            To break the controller from the loop and stop its work,
            the NEW_INCOMING_MESSAGE signal must be set after the EXIT_SIGNAL.

        Raises:
            ControllerException
        """

        self._set_the_signal()
        self._test_exception_after_signal()
        if EXIT_SIGNAL.wait():
            pass
