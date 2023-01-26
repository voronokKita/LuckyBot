""" Updater thread.
Integrated with Dispatcher, the main database and the Output Message Queue.
"""
from datetime import datetime, timezone

from lucky_bot.helpers.constants import UpdaterException
from lucky_bot.helpers.misc import CurrentTime, first_update_time, second_update_time, next_day_time
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, UPDATER_CYCLE, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.updater import update_dispatcher

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
            self.work_steps()
            self._set_the_signal()
            self._test_exception_after_signal()

            while True:
                wait = self._time_to_wait()
                if UPDATER_CYCLE.wait(wait):
                    pass
                if EXIT_SIGNAL.is_set():
                    break
                else:
                    self.work_steps()
                    self._test_updater_cycle()

        except Exception as exc:
            event.error('updater: exception')
            console('updater: exception')
            raise UpdaterException(exc)

    def work_steps(self):
        current_time = self._get_current_time()

        update_dispatcher.clear_all_users_flags(current_time)
        update_dispatcher.send_messages(current_time)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not UPDATER_CYCLE.is_set():
            UPDATER_CYCLE.set()
        super().merge()

    def _get_current_time(self) -> CurrentTime:
        current_time = CurrentTime()
        now = datetime.now(timezone.utc)
        update_one = first_update_time()
        update_two = second_update_time()

        if now < update_one:
            # Between 12 a.m. and the 1st update time.
            current_time.before_the_first_update = True
        elif update_one <= now < update_two:
            # After the 1st update time, before the 2nd.
            current_time.first_update = True
        elif update_two <= now:
            # After the 2nd update time, until the end of the day.
            current_time.second_update = True

        return current_time

    @staticmethod
    def _time_to_wait() -> int:
        """ Sleep after the dispatcher has worked out. """
        now = datetime.now(timezone.utc)
        update_one = first_update_time()
        update_two = second_update_time()

        if now < update_one:
            delta = update_one - now
            s = delta.total_seconds() + 10
            return s

        elif update_one <= now < update_two:
            delta = update_two - now
            s = delta.total_seconds() + 10
            return s

        elif update_two <= now:
            tomorrow = next_day_time()
            delta = tomorrow - now
            s = delta.total_seconds() + 10
            return s

    @staticmethod
    def _test_updater_cycle():
        pass
