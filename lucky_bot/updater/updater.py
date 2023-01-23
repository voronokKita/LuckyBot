""" Updater thread. """
from lucky_bot.helpers.constants import UpdaterException
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, UPDATER_CYCLE, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

# TODO reliable timing mechanism


class UpdaterThread(ThreadTemplate):
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def __str__(self):
        return 'updater thread'

    def body(self):
        """
        Description:
            0. Check the timing; send notifications or pass;
            1. Set the UPDATER_IS_RUNNING signal;
            2. Loop and wait for the UPDATER_CYCLE timing to pass.

            To break the updater from the loop and stop its work,
            the UPDATER_CYCLE signal must be set after the EXIT_SIGNAL.

        Raises:
            UpdaterException
        """
        try:
            self._send_messages()
            self._set_the_signal()
            self._test_exception_after_signal()

            while True:
                if UPDATER_CYCLE.wait(999):
                    pass
                if EXIT_SIGNAL.is_set():
                    break
                else:
                    self._send_messages()
                    self._test_updater_cycle()
        except Exception as exc:
            event.error('updater: exception')
            console('updater: exception')
            raise UpdaterException(exc)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not UPDATER_CYCLE.is_set():
            UPDATER_CYCLE.set()
        super().merge()

    def _send_messages(self):
        pass

    @staticmethod
    def _test_updater_cycle():
        pass
