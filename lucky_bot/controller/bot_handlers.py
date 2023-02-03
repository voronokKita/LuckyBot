"""
pyTelegramBotAPI update handlers.

* /start -> responder clears old data, inserts new user -> 'hello message'

* /restart -> responder clears old data, inserts new user -> 'hello message'

* /help -> responder -> 'help message'

* /ping -> responder -> 'pong'

* some text or wrong command -> responder -> 'help message'

* /add [text] -> parser inserts data -> responder -> 'OK or ERROR message'

* /update [number] [text] -> parser updates data -> responder -> 'OK or ERROR message'

* /delete [number, ...] -> responder deletes data -> 'OK or ERROR message'

* /list -> responder selects data -> 'list or none message'

* /show [number] -> responder selects data -> 'text or ERROR message'

Exceptions go through:
    DatabaseException
    OMQException
"""
import re

import logging
logger = logging.getLogger(__name__)
from logs import Log

from lucky_bot.helpers.constants import MASTER, TEXT_HELLO, TEXT_HELP, AdminExitSignal
from lucky_bot.helpers.signals import EXIT_SIGNAL
from lucky_bot.bot_init import BOT
from lucky_bot.controller import parser
from lucky_bot.controller import Respond

respond = Respond()


@BOT.message_handler(commands=['start', 'restart'])
def hello(message):
    Log.info('handler: /start')
    uid = message.chat.id

    respond.delete_user(uid, start_cmd=True)
    respond.add_user(uid)

    text = TEXT_HELLO.format(username=message.chat.username, help=TEXT_HELP)
    respond.send_message(uid, text)


@BOT.message_handler(commands=['add'])
def add_new_note(message):
    Log.info('handler: /add')
    message_text = message.text.removeprefix('/add').strip()
    if not message_text:
        help(message)
        return
    else:
        uid = message.chat.id
        result = parser.parse_note_and_insert(uid, message_text)
        if result:
            respond.send_message(uid, result)


@BOT.message_handler(commands=['update'])
def update_user_note(message):
    Log.info('handler: /update')
    parts = re.findall(r'(\d+)\s+(.+)', message.text, flags=re.DOTALL)
    if not parts:
        help(message)
        return
    note_num = parts[0][0]
    message_text = parts[0][1].strip()
    uid = message.chat.id

    result = parser.parse_note_and_update(uid, message_text, note_num)
    respond.send_message(uid, result)


@BOT.message_handler(commands=['delete'])
def delete_user_notes(message):
    """ Note: '/delete 1 2 text 3 4' results in [1,2,3,4] """
    Log.info('handler: /delete')
    notes_list = re.findall(r'(\d+)', message.text)
    if not notes_list:
        help(message)
        return
    else:
        respond.delete_notes(message.chat.id, notes_list)


@BOT.message_handler(commands=['list'])
def delete_user_notes(message):
    Log.info('handler: /list')
    respond.send_list(message.chat.id)


@BOT.message_handler(commands=['show'])
def show_user_note(message):
    Log.info('handler: /show')
    match = re.search(r'(/show)\s+(\d+)', message.text)
    if not match:
        help(message)
        return
    else:
        note_num = match.group(2)
        respond.send_note(message.chat.id, note_num)


@BOT.message_handler(commands=['ping'])
def ping(message):
    Log.info('handler: /ping')
    respond.send_message(message.chat.id, 'pong')


@BOT.message_handler(commands=['admin'])
def admin_commands(message):
    if str(message.chat.id) != MASTER:
        Log.info('handler: /admin - wrong master uid')
        return

    if re.search(r'(/admin)\s+(stop)', message.text):
        Log.info('handler: /admin stop')
        raise AdminExitSignal('stop')

    elif re.search(r'(/admin)\s+(users)', message.text):
        Log.info('handler: /admin users')
        respond.admin_count_users()

    elif re.search(r'(/admin)\s+(errors)', message.text):
        Log.info('handler: /admin errors')
        respond.admin_total_errors()

    elif re.search(r'(/admin)\s+(mail)', message.text):
        Log.info('handler: /admin mail')
        parts = re.findall(r'(/admin)\s+(mail)\s+(.+)', message.text, flags=re.DOTALL)
        if not parts:
            return
        message_text = parts[0][2].strip()
        respond.admin_mail_users(message_text)


@BOT.message_handler(commands=['help'])
@BOT.message_handler(content_types=['text'])
def help(message):
    Log.info('handler: /help')
    respond.send_message(message.chat.id, TEXT_HELP)
