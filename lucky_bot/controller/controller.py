""" Controller thread.
Integrated with Parser and Responder and
with Receiver through the Input Messages Queue.
"""
from lucky_bot.helpers.constants import ControllerException
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.helpers.misc import ThreadTemplate

from lucky_bot.receiver import InputQueue

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
            1. Clear INCOMING_MESSAGE, if set;
            2. Set the CONTROLLER_IS_RUNNING signal;
            3. Loop and wait for the NEW_INCOMING_MESSAGE signal.

            To break the controller from the loop and stop its work,
            the INCOMING_MESSAGE signal must be set after the EXIT_SIGNAL.

        Raises:
            ControllerException
        """
        try:
            self._check_new_messages()
            if INCOMING_MESSAGE.is_set():
                INCOMING_MESSAGE.clear()
            self._set_the_signal()
            self._test_exception_after_signal()

            while True:
                if INCOMING_MESSAGE.wait():
                    pass
                if EXIT_SIGNAL.is_set():
                    break
                self._check_new_messages()
                INCOMING_MESSAGE.clear()
                self._test_controller_cycle()

        except Exception as exc:
            event.error('controller: exception')
            console('controller: exception')
            raise ControllerException(exc)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not INCOMING_MESSAGE.is_set():
            INCOMING_MESSAGE.set()
        super().merge()

    def _check_new_messages(self):
        while True:
            msg_obj = InputQueue.get_first_message()
            if msg_obj:
                self._process_the_message(msg_obj)
                InputQueue.delete_message(msg_obj)
            else:
                break

    @staticmethod
    def _process_the_message(msg_obj):
        # TODO
        pass

    @staticmethod
    def _test_controller_cycle():
        pass
