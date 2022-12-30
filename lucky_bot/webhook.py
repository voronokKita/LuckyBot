from telebot import TeleBot
from pyngrok import ngrok
from pyngrok.ngrok import NgrokTunnel
from pyngrok.exception import PyngrokNgrokURLError
from werkzeug.serving import make_server, BaseWSGIServer

from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING, WEBHOOK_IS_STOPPED
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

    tunnel: NgrokTunnel = None
    webhook_url: str = None
    webhook: bool = False
    server: BaseWSGIServer = None
    serving: bool = False

    def __str__(self):
        return 'webhook thread'

    def body(self):
        try:
            self._make_tunnel()
            self._set_webhook()
            self._make_server()

            self._set_the_signal()
            self._test_exception()

            self.serving = True
            self._test_exception_after_serving()
            self._start_server()

        except Exception as exc:
            raise WebhookException(exc)
        finally:
            self.serving = False
            self._close_connections()

    def merge(self):
        self._shutdown()
        super().merge()

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

    def _start_server(self):
        ''' Wrapped for testing. '''
        self.server.serve_forever(poll_interval=2)

    def _close_connections(self):
        if self.webhook:
            self._remove_webhook()
        if self.tunnel:
            self._close_tunnel()

    def _shutdown(self):
        if self.serving:
            self.server.shutdown()
        elif self.server:
            self.server.socket.close()

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

    @staticmethod
    def _test_exception_after_serving():
        pass
