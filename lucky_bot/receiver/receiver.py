""" Receiver thread.
Integrated with the Flask app and the Input Message Queue.
"""
from pyngrok import ngrok
from pyngrok.ngrok import NgrokTunnel
from pyngrok.exception import PyngrokNgrokURLError
from werkzeug.serving import make_server, BaseWSGIServer

from lucky_bot.helpers.constants import (
    REPLIT, REPLIT_URL, ADDRESS, PORT,
    WEBHOOK_ENDPOINT, WEBHOOK_SECRET,
    ReceiverException,
)
from lucky_bot.helpers.signals import RECEIVER_IS_RUNNING, RECEIVER_IS_STOPPED
from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot import BOT

from lucky_bot.receiver import FLASK_APP

import logging
logger = logging.getLogger(__name__)
from logs import Log


class Receiver:
    tunnel: NgrokTunnel = None
    webhook_url: str = None
    webhook: bool = False
    server: BaseWSGIServer = None
    serving: bool = False

    def connect(self):
        self._make_tunnel()
        self._set_webhook()
        self._make_server()

    def start_server(self):
        self.server.serve_forever(poll_interval=2)

    def disconnect(self):
        if self.webhook:
            self._remove_webhook()
            self.webhook = False
            self.webhook_url = None
        if self.tunnel:
            self._close_tunnel()
            self.tunnel = None

    def final_clean_up(self):
        if self.server:
            self._shutdown_server()
        if self.tunnel or self.webhook:
            self.disconnect()

    def _make_tunnel(self):
        if REPLIT:
            self.webhook_url = REPLIT_URL + WEBHOOK_ENDPOINT
        else:
            self.tunnel = ngrok.connect(PORT, proto='http', bind_tls=True)
            Log.console(str(self.tunnel))
            self.webhook_url = self.tunnel.public_url + WEBHOOK_ENDPOINT

    def _set_webhook(self):
        # The old session might not remove the webhook in case of an exception.
        self._remove_webhook()

        self.webhook = BOT.set_webhook(
            url=self.webhook_url,
            max_connections=10,
            secret_token=WEBHOOK_SECRET,
        )
        if self.webhook is not True:
            raise ReceiverException(f"Can't set the webhook: {self.webhook}")

    def _make_server(self):
        self.server = make_server(
            host=ADDRESS,
            port=PORT,
            app=FLASK_APP,
            threaded=False,
            processes=1,
        )

    def _remove_webhook(self):
        """ Wrapped for testing. """
        BOT.remove_webhook()

    def _shutdown_server(self):
        if self.server and self.serving:
            self.server.shutdown()
            self.serving = False
        elif self.server and not self.serving:
            # it may happen in some cases
            self.server.socket.close()
        self.server = None

    def _close_tunnel(self):
        """ Formally, ngrok doesn't need to be closet, but let it be. """
        if REPLIT:
            return
        try: ngrok.disconnect(self.tunnel.public_url)
        except (PyngrokNgrokURLError, Exception): pass
        finally: ngrok.kill()


class ReceiverThread(ThreadTemplate):
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED

    receiver = Receiver()

    def __str__(self):
        return 'receiver thread'

    def body(self):
        """ A simplified workflow:
        0. Set up a http tunnel;
        1. Notify Telegram about the tunnel;
        2. Make a werkzeug server. Need a Flask app;
        3. Set the RECEIVER_IS_RUNNING signal;
        4. Call the serve_forever() method; Wait for a shutdown() call...

        Finally, after normal shutdown or an exception, a notification must be sent to
        Telegram to remove the webhook, and a tunnel must be closed.

        Raises:
            ReceiverException
        """
        try:
            self.receiver.connect()

            self._set_the_signal()
            self._test_exception_after_signal()

            self.receiver.serving = True
            self._test_exception_after_serving()

            # here the thread is waiting for a server.shutdown() call
            self.receiver.start_server()

        except Exception as exc:
            raise ReceiverException(exc)
        finally:
            # after server shutdowns either way
            self.receiver.serving = False
            self.receiver.disconnect()

    def merge(self):
        self.receiver.final_clean_up()
        super().merge()

    @staticmethod
    def _test_exception_after_serving():
        pass
