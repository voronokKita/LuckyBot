from pyngrok import ngrok
from pyngrok.exception import PyngrokNgrokURLError

from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.helpers.constants import REPLIT, REPLIT_URL, WEBHOOK_ENDPOINT, PORT, TESTING

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


class WebhookThread(ThreadTemplate):
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    tunnel = None
    webhook_url = None

    def __str__(self):
        return 'webhook thread'

    def body(self):
        self._make_tunnel()

        self._set_the_signal()
        self._test_exception()
        if EXIT_SIGNAL.wait():
            pass

        self._close_tunnel()

    def _make_tunnel(self):
        if REPLIT:
            self.webhook_url = REPLIT_URL + WEBHOOK_ENDPOINT
        else:
            self.tunnel = ngrok.connect(PORT, proto='http', bind_tls=True)
            console(self.tunnel)
            self.webhook_url = self.tunnel.public_url + WEBHOOK_ENDPOINT

    def _close_tunnel(self):
        try:
            ngrok.disconnect(self.tunnel.public_url)
        except (PyngrokNgrokURLError, Exception):
            pass
        ngrok.kill()
