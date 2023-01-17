""" pyTelegramBotAPI update handlers. """
import time

import logging
from logs import console, event
logger = logging.getLogger(__name__)

from lucky_bot.bot_init import BOT
from lucky_bot.controller import Respond

respond = Respond()

TEXT_HELLO = '''Hello, @{username}!

ⓘ The server may be slow so don't rush to use commands again if there is no immediate response. (´･ᴗ･ ` )

{help}'''

TEXT_HELP = f"ⓘ Some help message"


@BOT.message_handler(commands=['start', 'restart'])
def hello(message):
    event.info('message: /start')
    console('message: /start')
    uid = message.chat.id

    respond.delete_user(uid, start_cmd=True)
    text = TEXT_HELLO.format(username=message.chat.username, help=TEXT_HELP)
    respond.send_message(uid, text)


@BOT.message_handler(content_types=['text'])
@BOT.message_handler(commands=['help'])
def help(message):
    respond.send_message(message.chat.id, TEXT_HELP)
