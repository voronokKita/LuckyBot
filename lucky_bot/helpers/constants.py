""" All the constants, setting variables and exceptions are here. """
import os
import re
import sys
import pathlib


REPLIT = False
PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

if not REPLIT and [arg for arg in sys.argv if 'test' in arg]:
    TESTING = True
else:
    TESTING = False


# Help
TEXT_HELLO = '''(*・ω・)ﾉ" Hello, @{username}!
This bot was made to remind you.
You can save text notes in the database. A couple of times a day I will take a random note and send it to you.
All notes are stored in an encrypted form.

ⓘ The server may be slow so don't rush to use commands again if there is no immediate response. (´･ᴗ･ ` )

{help}'''

TEXT_HELP = '''ⓘ Commands:
/add [text] — save the note to the database
/list — will send you a list of saved notes with their numbers
/show [number] — will send you a saved note
/update [number] [text] — replace the note N with the new text
/delete [number, ...] — delete the notes with the specified numbers
/restart
/help
/ping

ⓘ Text markup:
<b>bold</b>
<i>italic</i>
<u>underline</u>
<code>monospace code</code>
'''


# Databases
LAST_NOTES_LIST = 10

if TESTING:
    ''' Note:
    :memory: does not always work, because some parts are 
    running in subprocesses, i.e. in another memory areas.
    '''
    DB_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_imq.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_omq.sqlite3'
else:
    DB_FILE = PROJECT_DIR / 'data' / 'data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'data' / 'input_message_queue.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'data' / 'output_message_queue.sqlite3'


# Web settings
REPLIT_URL = 'https://LuckyBot.kitavoronok.repl.co'
PORT = 5000
ADDRESS = '0.0.0.0'
WEBHOOK_ENDPOINT = '/webhook'
WEBHOOK_WAS_SET = re.compile('was set|already set')

if not REPLIT:
    api = PROJECT_DIR / 'resources' / '.tgapi'
    with api.open('r') as f: API = f.read().strip()

    webhook_secret = PROJECT_DIR / 'resources' / '.webhook_secret_token'
    with webhook_secret.open('r') as f: WEBHOOK_SECRET = f.read().strip()

else:
    API = os.environ['TGAPI']
    WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']


# Cryptography
if not REPLIT:
    fernet_secret = PROJECT_DIR / 'resources' / '.fernet_secret_key'
    with fernet_secret.open('rb') as f: ENCRYPTION_KEY = f.read()

    salt = PROJECT_DIR / 'resources' / '.salt'
    with salt.open('rb') as f: SALT = f.read()

else:
    ENCRYPTION_KEY = os.environ['FERNET_SECRET'].encode()
    SALT = os.environ['SALT'].encode()


# Admin
if not REPLIT:
    master = PROJECT_DIR / 'resources' / '.master'
    with master.open('r') as f: MASTER = f.read().strip()
else:
    MASTER = os.environ['MASTER']


# Logs
LOG_LIMIT = 1000
LOG_EVENTS_FILE = PROJECT_DIR / 'logs' / 'events.log'
LOG_EXCEPTIONS_FILE = PROJECT_DIR / 'logs' / 'exceptions.log'
LOG_WERKZEUG_FILE = PROJECT_DIR / 'logs' / 'werkzeug.log'
LOG_TELEBOT_FILE = PROJECT_DIR / 'logs' / 'pyTelegramBotAPI.log'
ERRORS_TOTAL = PROJECT_DIR / 'logs' / 'errors_total'
if not ERRORS_TOTAL.exists():
    with ERRORS_TOTAL.open('w') as f: f.write('0')


# Main
TREAD_RUNNING_TIMEOUT = 30


# Telegram request errors
'''
400 - Bad Request: chat not found
400 - Bad request: user not found
400 - Bad request: Group migrated to supergroup
400 - Bad request: Invalid file id
400 - Bad request: Message not modified
400 - Bad request: Wrong parameter action in request
401 - Unauthorized
403 - Forbidden: user is deactivated
403 - Forbidden: bot was kicked
403 - Forbidden: bot blocked by user
403 - Forbidden: bot can't send messages to bots
409 - Conflict: Terminated by other long poll
429 - Too many requests
'''
TG_WRONG_TOKEN = re.compile('Unauthorized')
TG_UID_NOT_FOUND = re.compile('not found')
TG_BOT_BLOCKED = re.compile('kicked|blocked|deactivated')
TG_BOT_TIMEOUT = re.compile('Too many requests')


# Exceptions
class TestException(Exception):
    """ For testing purposes. """

class DatabaseException(Exception):
    """ Something wrong in the main database. """

class MainException(Exception):
    """ For main.py """

class ThreadException(Exception):
    """ Normal exception for the threads, except main. """


class UpdaterException(ThreadException):
    """ Something wrong in the updater. """

class UpdateDispatcherException(UpdaterException):
    """ Something wrong in Updater's dispatcher. """


class ReceiverException(ThreadException):
    """ Something wrong in the receiver. """

class FlaskException(ReceiverException):
    """ Something wrong in the flask app. """

class WebhookWrongRequest(FlaskException):
    """ Wrong request format. """

class IMQException(ReceiverException):
    """ Something wrong in the input message queue. """


class ControllerException(ThreadException):
    """ Something wrong in the controller. """

class AdminExitSignal(ControllerException):
    """ An admin exit command in the bot handler. """

class TelebotHandlerException(ControllerException):
    """ Something wrong in the telebot handlers. """


class SenderException(ThreadException):
    """ Something wrong in the sender. """

class StopTheSenderGently(SenderException):
    """ Exit from the sender body() without an exception. """

class OMQException(SenderException):
    """ Something wrong in the output message queue. """

class OutputDispatcherException(SenderException):
    """ Something wrong in Sender's dispatcher. """

class DispatcherWrongToken(OutputDispatcherException):
    """ Wrong API token from ApiTelegramException. """

class DispatcherNoAccess(OutputDispatcherException):
    """ "Uid not found" or "bot blocked" from ApiTelegramException. """

class DispatcherTimeout(OutputDispatcherException):
    """ Timeout ApiTelegramException. """

class DispatcherUndefinedExc(OutputDispatcherException):
    """ Undefined ApiTelegramException. """
