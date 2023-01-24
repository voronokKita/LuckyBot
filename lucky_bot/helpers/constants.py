""" All the constants, setting variables and exceptions are here. """
import os
import re
import sys
import pathlib
from datetime import datetime, timezone


REPLIT = False
PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

if not REPLIT and [arg for arg in sys.argv if 'test' in arg]:
    TESTING = True
else:
    TESTING = False

# Databases
if TESTING:
    ''' Note:
    :memory: db is not working, because
    a werkzeug server - make_server(), - is running in another process,
    i.e. in another memory area.
    '''
    DB_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_imq.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_omq.sqlite3'
else:
    DB_FILE = PROJECT_DIR / 'data' / 'data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'data' / 'input_message_queue.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'data' / 'output_message_queue.sqlite3'

LAST_NOTES_LIST = 10

# Web settings
REPLIT_URL = 'https://LuckyBot.kitavoronok.repl.co'
PORT = 5000
ADDRESS = '0.0.0.0'
WEBHOOK_ENDPOINT = '/webhook'
WEBHOOK_WAS_SET = re.compile('was set|already set')

if not REPLIT:
    API = PROJECT_DIR / 'resources' / '.tgapi'
    with open(API) as f:
        API = f.read().strip()
else:
    API = os.environ['TGAPI']

WEBHOOK_SECRET = PROJECT_DIR / 'resources' / '.webhook_secret_token'
with open(WEBHOOK_SECRET) as f:
    WEBHOOK_SECRET = f.read().strip()

# Logs
LOG_LIMIT = 1000
LOG_EVENTS_FILE = PROJECT_DIR / 'logs' / 'events.log'
LOG_EXCEPTIONS_FILE = PROJECT_DIR / 'logs' / 'exceptions.log'
LOG_WERKZEUG_FILE = PROJECT_DIR / 'logs' / 'werkzeug.log'
LOG_TELEBOT_FILE = PROJECT_DIR / 'logs' / 'pyTelegramBotAPI.log'

# Main
TREAD_RUNNING_TIMEOUT = 30

# Updater
FIRST_UPDATE = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
SECOND_UPDATE = datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0)

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

class MainException(Exception):
    """ For a main.py """

class ThreadException(Exception):
    """ Normal exception for the threads, except main. """


class ReceiverException(ThreadException):
    """ Something wrong in the receiver thread. """

class FlaskException(Exception):
    """ Something wrong in the flask app. """

class WebhookWrongRequest(FlaskException):
    """ Wrong request format. """


class SenderException(ThreadException):
    """ Something wrong in the sender thread. """

class StopTheSenderGently(SenderException):
    """ Exit from the sender body() without an exception. """


class DispatcherException(Exception):
    """ Something wrong in the dispatcher. """

class DispatcherWrongToken(DispatcherException):
    """ Wrong API token from ApiTelegramException. """

class DispatcherNoAccess(DispatcherException):
    """ "Uid not found" or "bot blocked" from ApiTelegramException. """

class DispatcherTimeout(DispatcherException):
    """ Timeout ApiTelegramException. """

class DispatcherUndefinedExc(DispatcherException):
    """ Undefined ApiTelegramException. """


class ControllerException(Exception):
    """ Something wrong in the controller. """

class TelebotHandlerException(ControllerException):
    """ Something wrong in the telebot handlers. """


class UpdaterException(Exception):
    """ Something wrong in the updater. """
