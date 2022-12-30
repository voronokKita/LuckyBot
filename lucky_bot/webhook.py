from telebot import TeleBot
from pyngrok import ngrok
from pyngrok.exception import PyngrokNgrokURLError
from werkzeug.serving import make_server

from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED, EXIT_SIGNAL
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.helpers.constants import (
    REPLIT, REPLIT_URL, WEBHOOK_ENDPOINT,
    ADDRESS, PORT, API, WEBHOOK_SECRET, WebhookException,
)
from lucky_bot.flask_config import FLASK_APP

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


class WebhookThread(ThreadTemplate):
    is_running_signal = WEBHOOK_IS_RUNNING
    is_stopped_signal = WEBHOOK_IS_STOPPED

    tunnel = None
    webhook_url = None
    webhook = False
    server = None

    def __str__(self):
        return 'webhook thread'

    def body(self):
        try:
            self._make_tunnel()
            self._set_webhook()

            self._set_the_signal()
            self._test_exception()

            self.server.serve_forever()

        except Exception as exc:
            raise WebhookException(exc)
        finally:
            self._close_connections()

    def _make_tunnel(self):
        if REPLIT:
            self.webhook_url = REPLIT_URL + WEBHOOK_ENDPOINT
        else:
            self.tunnel = ngrok.connect(PORT, proto='http', bind_tls=True)
            console(self.tunnel)
            self.webhook_url = self.tunnel.public_url + WEBHOOK_ENDPOINT

    def _set_webhook(self):
        self._remove_webhook()

        self.webhook = TeleBot(API, threaded=False).set_webhook(
            url=self.webhook_url,
            max_connections=10,
            secret_token=WEBHOOK_SECRET,
        )
        if self.webhook is not True:
            raise WebhookException(f"Can't set the webhook: {self.webhook}")

    def _make_server(self):
        self.server = make_server(
            host=ADDRESS,
            port=PORT,
            app=FLASK_APP,
        )

    def _close_connections(self):
        if self.server:  # TODO
            self.shutdown()
        if self.webhook:
            self._remove_webhook()
        if self.tunnel:
            self._close_tunnel()

    def shutdown(self):
        self.server.shutdown()

    @staticmethod
    def _remove_webhook():
        TeleBot(API, threaded=False).remove_webhook()

    def _close_tunnel(self):
        ''' Formally, ngrok doesn't need to be closet, but let it be. '''
        try:
            ngrok.disconnect(self.tunnel.public_url)
        except (PyngrokNgrokURLError, Exception):
            pass
        ngrok.kill()

