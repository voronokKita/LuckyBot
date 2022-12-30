import secrets
from random import randint

import telebot
import flask
from flask import Flask, request

from lucky_bot.helpers.constants import WEBHOOK_ENDPOINT, WebhookWrongRequest
from lucky_bot.helpers.signals import NEW_TELEGRAM_MESSAGE

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


FLASK_APP = Flask('flask_webhook')
FLASK_APP.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    PROPAGATE_EXCEPTIONS=True,
    SECRET_KEY=secrets.token_urlsafe(randint(100, 256)),
    LOGGER_NAME=__name__,
    MAX_CONTENT_LENGTH=10*1024*1024,
    # TRAP_HTTP_EXCEPTIONS=True,
    # TRAP_BAD_REQUEST_ERRORS=True,
)


@FLASK_APP.route(WEBHOOK_ENDPOINT, methods=['POST'])
def inbox():
    try:
        if not request.headers.get('content-type') == 'application/json':
            raise WebhookWrongRequest
        try:
            data = request.get_data().decode('utf-8')
            telebot.types.Update.de_json(data)
        except Exception:
            raise WebhookWrongRequest

    except WebhookWrongRequest:
        msg = f'wrong webhook request: {request.get_data().decode("utf-8")}'
        console(msg)
        event.warning(msg)
        flask.abort(400)

    else:
        # print(data)
        NEW_TELEGRAM_MESSAGE.set()
        return '', 200


@FLASK_APP.route('/ping', methods=['GET'])
def ping():
    return 'pong', 200
