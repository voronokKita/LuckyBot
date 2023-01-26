""" If it's not a constant, a setting variable, an exception, or a signal, then it goes here. """
import threading
from datetime import datetime, timezone, timedelta

from lucky_bot.helpers.constants import ThreadException
from lucky_bot.helpers.signals import EXIT_SIGNAL


def first_update_time() -> datetime:
    """ 12 p.m. UTC """
    return datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)


def second_update_time() -> datetime:
    """ 18 p.m. UTC """
    return datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0)


def next_day_time() -> datetime:
    """ 12 a.m. UTC """
    t = datetime.now(timezone.utc)
    t += timedelta(days=1)
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


class CurrentTime:
    before_the_first_update = False
    first_update = False
    second_update = False


class ThreadTemplate(threading.Thread):
    """
    Base class for all the threads.

    Attributes:
        is_running_signal (threading.Event): an Event for this thread to start its work
        is_stopped_signal (threading.Event): an Event for this thread to stop its work
        exception (None): if an exception is caught, it will be saved here and raised after self.merge()

    Notes:
        The Events for the thread must be specified in a child class.
        The start and stop events behave differently in each thread.
        A thread may need to do some work before signaling its start.
        And after the stop signal, it may take a few ticks
        before the self.is_alive() will return False.
    """
    exception = None
    is_running_signal = None
    is_stopped_signal = None

    def __int__(self):
        threading.Thread.__init__(self)

    def body(self):
        """ All work goes here. Must be overwritten in a child class. """
        self._set_the_signal()
        self._test_exception_after_signal()
        if EXIT_SIGNAL.wait():
            pass

    def run(self):
        """
        Will run the thread.
        After the thread either finishes its work or raises an exception,
        the self.is_stopped_signal will be set.
        """
        try:
            self._test_exception_before_signal()
            self.body()
        except Exception as e:
            self.exception = e
            EXIT_SIGNAL.set()
        finally:
            self.is_stopped_signal.set()

    def merge(self):
        """
        Will stop the work and call the Thread.join(self)
        Will raise an exception, if any.
        All Exceptions declared in helpers.constants.py
        """
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if self.is_stopped_signal.wait(10):
            pass

        threading.Thread.join(self, 5)

        if self.exception:
            raise self.exception
        elif self.is_alive():
            raise ThreadException(f'Stop timeout: {self}.')

    @classmethod
    def _set_the_signal(cls):
        """ Signal is wrapped for testing purposes. """
        cls.is_running_signal.set()

    @staticmethod
    def _test_exception_before_signal():
        pass

    @staticmethod
    def _test_exception_after_signal():
        pass
