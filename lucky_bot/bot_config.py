import telebot

from lucky_bot.helpers.constants import API

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


BOT = telebot.TeleBot(API, threaded=False)


def send_message(uid:int, text:str, file=None) -> bool:
    BOT.send_message(uid, text)
    return True
