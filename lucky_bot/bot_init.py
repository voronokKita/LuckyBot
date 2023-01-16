""" pyTelegramBotAPI initialisation. """
import telebot

from lucky_bot.helpers.constants import API

import logging
logger = logging.getLogger(__name__)


BOT = telebot.TeleBot(API, threaded=False)
