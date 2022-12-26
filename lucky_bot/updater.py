import threading

from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, EXIT_SIGNAL


class UpdaterThread(threading.Thread):
    exception = None

    def __str__(self):
        return 'updater thread'

    def __int__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            # TODO

            UPDATER_IS_RUNNING.set()

            self._test_exception()

            if EXIT_SIGNAL.wait():
                pass

        except Exception as e:
            self.exception = e

    def stop(self):
        threading.Thread.join(self, 1)
        if self.exception:
            raise self.exception

    @staticmethod
    def _test_exception():
        pass
