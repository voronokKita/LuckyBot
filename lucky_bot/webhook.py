from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate


class WebhookThread(ThreadTemplate):
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    def __str__(self):
        return 'webhook thread'

    def body(self):
        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass
