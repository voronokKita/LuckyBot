from datetime import datetime, timezone

from lucky_bot.helpers.constants import (
    UpdaterException, DatabaseException,
    UpdateDispatcherException, OMQException,
)
from lucky_bot.helpers.misc import (
    CurrentTime, first_update_time,
    second_update_time, next_day_time,
)
from lucky_bot.helpers.signals import (
    UPDATER_IS_RUNNING, UPDATER_IS_STOPPED,
    UPDATER_CYCLE, EXIT_SIGNAL,
)
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.updater import update_dispatcher

import logging
logger = logging.getLogger(__name__)
from logs.config import Log


class Updater:
    """ Makes calls to the update dispatcher. """

    @classmethod
    def works(cls):
        """
        Raises:
            UpdateDispatcherException
            DatabaseException: propagation
            OMQException: propagation
        """
        current_time = cls._get_current_time()
        try:
            update_dispatcher.clear_all_users_flags(current_time)
            update_dispatcher.send_messages(current_time)

        except (DatabaseException, OMQException) as exc:
            raise exc
        except Exception as exc:
            msg = 'updater: exception in the update dispatcher'
            Log.error(msg)
            raise UpdateDispatcherException(exc)

    @staticmethod
    def _get_current_time() -> CurrentTime:
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


class UpdaterThread(ThreadTemplate):
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def __str__(self):
        return 'updater thread'

    def body(self):
        """
        Description:
            0. Send messages or pass;
            1. Set the UPDATER_IS_RUNNING signal;
            2. Loop and wait for the UPDATER_CYCLE timing to pass.

            To break the updater from the loop and stop its work,
            the UPDATER_CYCLE signal must be set after the EXIT_SIGNAL.

        Raises:
            UpdaterException
            UpdateDispatcherException: propagation
            DatabaseException: propagation
            OMQException: propagation
        """
        try:
            Updater.works()

            self._set_the_signal()
            self._test_exception_after_signal()

            while True:
                if UPDATER_CYCLE.is_set():
                    UPDATER_CYCLE.clear()

                wait = self._time_to_wait()
                if UPDATER_CYCLE.wait(wait):
                    pass

                if EXIT_SIGNAL.is_set():
                    break
                else:
                    Updater.works()
                    self._test_updater_cycle()

        except (UpdateDispatcherException, DatabaseException, OMQException) as exc:
            raise exc
        except Exception as exc:
            Log.error('updater: a normal exception')
            raise UpdaterException(exc)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not UPDATER_CYCLE.is_set():
            UPDATER_CYCLE.set()
        super().merge()

    @staticmethod
    def _time_to_wait() -> int:
        """ Time to sleep after the update dispatcher has worked out. """
        now = datetime.now(timezone.utc)
        update_one = first_update_time()
        update_two = second_update_time()

        if now < update_one:
            timedelta = update_one - now
            s = timedelta.total_seconds() + 10
            return s

        elif update_one <= now < update_two:
            timedelta = update_two - now
            s = timedelta.total_seconds() + 10
            return s

        elif update_two <= now:
            tomorrow = next_day_time()
            timedelta = tomorrow - now
            s = timedelta.total_seconds() + 10
            return s

    @staticmethod
    def _test_updater_cycle():
        pass
