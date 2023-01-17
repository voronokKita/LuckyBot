""" pyTelegramBotAPI update handlers. """
import time

import logging
from logs import console, event
logger = logging.getLogger(__name__)

from lucky_bot.bot_init import BOT
from lucky_bot.controller import parser
from lucky_bot.controller import Respond

respond = Respond()

''' Commands

Tg message DONE
/start -> responder clears old data, insert new uer -> 'hello message'

Tg message DONE
/restart -> responder clears old data, insert new uer -> 'hello message'

Tg message DONE
/help -> responder -> 'help message'

Tg message DONE
some text or wrong command -> responder -> 'help message'

Tg message
/add [text] -> parser inserts data -> responder -> 'OK or ERROR message'

Tg message
/update [number] [text] -> parser updates data -> responder -> 'OK or ERROR message'

Tg message
/delete [number, n+1] -> responder deletes data -> 'OK or ERROR message'

Tg message
/list -> responder selects data -> 'list or ERROR message'

Tg message
/show [number] -> responder selects data -> 'text or ERROR message'
'''

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


@BOT.message_handler(commands=['add'])
def add_new_note(message):
    uid = message.chat.id
    message_text = message.text.removeprefix('/add').strip()
    if not message_text:
        help(message)
        return

    result = parser.parse_note_and_insert(message_text)
    respond.send_message(uid, result)


@BOT.message_handler(commands=['help'])
@BOT.message_handler(content_types=['text'])
def help(message):
    respond.send_message(message.chat.id, TEXT_HELP)

