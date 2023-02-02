""" Flask based webhook.
Calls the input message queue to save a telegram message data.
"""
import json
import secrets
from random import randint

import telebot
import flask
from flask import Flask, request

from lucky_bot.helpers.constants import (
    WEBHOOK_ENDPOINT, WEBHOOK_SECRET,
    WebhookWrongRequest, FlaskException, IMQException,
)
from lucky_bot.helpers.signals import INCOMING_MESSAGE, EXIT_SIGNAL

from lucky_bot.receiver import InputQueue

import logging
logger = logging.getLogger(__name__)
from logs import Log

def test_exception(): pass


FLASK_APP = Flask('flask_webhook')
FLASK_APP.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    PROPAGATE_EXCEPTIONS=True,
    LOGGER_NAME='flask_webhook',
    SECRET_KEY=secrets.token_urlsafe(randint(40, 60)),
    MAX_CONTENT_LENGTH=15*1024*1024,
)


def get_message_data() -> str:
    """
    Ensures that a request and its data both are correct.
    Raises: WebhookWrongRequest
    """
    h1 = request.headers.get('content-type')
    h2 = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    if not h1 == 'application/json' and h2 == WEBHOOK_SECRET:
        raise WebhookWrongRequest
    try:
        data = request.get_data().decode('utf-8')
        telebot.types.Update.de_json(data)
    except Exception:
        raise WebhookWrongRequest
    else:
        return data


def save_message_to_queue(data):
    """
    Tries to save a message data to the Input Message Queue.
    Raises:
        FlaskException
        IMQException: propagation
    """
    try:
        test_exception()
        d = json.loads(data)
        time = d['message']['date']
        InputQueue.add_message(data, time)

    except IMQException as exc:
        EXIT_SIGNAL.set()
        raise exc
    except Exception as exc:
        logger.exception('flask: error saving message to imq')
        Log.error('flask: error saving message to imq')
        EXIT_SIGNAL.set()
        raise FlaskException(exc)


@FLASK_APP.route(WEBHOOK_ENDPOINT, methods=['POST'])
def inbox():
    """
    Exceptions go through:
        IMQException

    Raises:
        FlaskException
    """
    try:
        data = get_message_data()

    except WebhookWrongRequest:
        msg = 'flask: wrong request: %s' % request.get_data().decode('utf-8')
        Log.warning(msg)
        flask.abort(400)
    except Exception as exc:
        logger.exception('flask: error parsing request')
        Log.error('flask: error parsing request')
        EXIT_SIGNAL.set()
        raise FlaskException(exc)

    else:
        save_message_to_queue(data)
        INCOMING_MESSAGE.set()
        Log.console('new tg message')
        return '', 200


@FLASK_APP.route('/ping', methods=['GET'])
def ping():
    return 'pong', 200
