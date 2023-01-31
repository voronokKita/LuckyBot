""" pyTelegramBotAPI initialisation for another modules. """
import telebot

from lucky_bot.helpers.constants import API

import logging
logger = logging.getLogger(__name__)


class ExceptionHandler(telebot.ExceptionHandler):
    """ Currently not in use. """
    def handle(self, exception):
        pass


BOT = telebot.TeleBot(API, threaded=False)
