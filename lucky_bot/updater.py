from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate


class UpdaterThread(ThreadTemplate):
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def __str__(self):
        return 'updater thread'

    def body(self):
        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass
