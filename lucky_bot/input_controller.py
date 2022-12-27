from lucky_bot.helpers.signals import INPUT_CONTROLLER_IS_RUNNING, INPUT_CONTROLLER_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate


class InputControllerThread(ThreadTemplate):
    is_running_signal = INPUT_CONTROLLER_IS_RUNNING
    is_stopped_signal = INPUT_CONTROLLER_IS_STOPPED

    def __str__(self):
        return 'input controller thread'

    def body(self):
        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass
