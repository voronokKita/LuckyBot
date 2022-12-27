from lucky_bot.helpers.signals import SENDER_IS_RUNNING, SENDER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate


class SenderThread(ThreadTemplate):
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def __str__(self):
        return 'sender thread'

    def body(self):
        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass
