""" pyTelegramBotAPI update handlers. """
import time

import logging
from logs import console, event
logger = logging.getLogger(__name__)

from lucky_bot.bot_init import BOT
from lucky_bot.controller import Respond

respond = Respond()


TEXT_HELLO = f"ⓘ The server may be slow so don't rush to use commands again " \
             "if there is no immediate response. (´･ᴗ･ ` )"

TEST_HELP = f"Some help message"


@BOT.message_handler(commands=['start', 'restart'])
def hello(message):
    event.info('message: /start')
    console('message: /start')
    uid = message.chat.id
    respond.delete_user(uid, start_cmd=True)

    respond.send_message(uid, f'Hello, @{message.chat.username}!')
    time.sleep(0.5)
    respond.send_message(uid, TEXT_HELLO)
    time.sleep(0.5)
    respond.send_message(uid, TEST_HELP)
