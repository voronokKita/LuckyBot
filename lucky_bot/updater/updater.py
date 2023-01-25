""" Updater thread. """
import random
from time import time
from datetime import datetime, timezone

from lucky_bot.helpers.constants import UpdaterException, FIRST_UPDATE, SECOND_UPDATE
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, UPDATER_CYCLE, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.sender import OutputQueue
from lucky_bot import MainDB

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


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
                wait = self._time_to_wait()
                if UPDATER_CYCLE.wait(wait):
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
        ''' TODO '''
        if not self._it_is_time():
            return
        else:
            self._notifications_dispatcher()

    @staticmethod
    def _notifications_dispatcher():
        ''' TODO '''
        users = MainDB.get_users_with_notes()
        if not users:
            return
        for user in users:
            notes = MainDB.get_notifications_for_the_updater(user.tg_id)
            if not notes:
                msg = f"updater: get a user that don't have any notes to send, id #{user.id}"
                console(msg)
                event.warning(msg)
                continue

            note = random.choice(notes)
            OutputQueue.add_message(user.tg_id, note.text, int(time()))

    @staticmethod
    def _it_is_time() -> bool:
        ''' TODO '''
        current_time = datetime.now(timezone.utc)
        if FIRST_UPDATE <= current_time or SECOND_UPDATE <= current_time:
            return True
        else:
            return False

    @staticmethod
    def _time_to_wait() -> int:
        ''' TODO '''
        current_time = datetime.now(timezone.utc)
        if FIRST_UPDATE <= current_time:
            h = SECOND_UPDATE.hour - current_time.hour
            m = current_time.minute
            s = h * 3600 + m * 60 + current_time.second + 10
            return s
        elif SECOND_UPDATE <= current_time:
            pass

    @staticmethod
    def _test_updater_cycle():
        pass
