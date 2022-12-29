import threading

from lucky_bot.helpers.signals import EXIT_SIGNAL
from lucky_bot.helpers.constants import ThreadException


class ThreadTemplate(threading.Thread):
    exception = None
    is_running_signal = None
    is_stopped_signal = None

    def __int__(self):
        threading.Thread.__init__(self)

    def body(self):
        ''' Must be overwritten. '''
        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass

    def run(self):
        try:
            self._test_exception_before_signal()
            self.body()
        except Exception as e:
            self.exception = e
            EXIT_SIGNAL.set()
        finally:
            self.is_stopped_signal.set()

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if self.is_stopped_signal.wait(10):
            pass
        threading.Thread.join(self, 5)
        if self.exception:
            raise ThreadException(self.exception)
        elif self.is_alive():
            raise ThreadException(f'Stop timeout: {self}.')

    @staticmethod
    def _test_exception():
        pass

    @staticmethod
    def _test_exception_before_signal():
        pass

    @classmethod
    def _set_the_signal(cls):
        ''' Signal is wrapped for testing purposes. '''
        cls.is_running_signal.set()

