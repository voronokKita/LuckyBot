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
    imq_secret = PROJECT_DIR / 'resources' / '.imq_secret_key'
    with imq_secret.open('rb') as f: IMQ_SECRET = f.read()

    omq_secret = PROJECT_DIR / 'resources' / '.omq_secret_key'
    with omq_secret.open('rb') as f: OMQ_SECRET = f.read()

    db_secret = PROJECT_DIR / 'resources' / '.db_secret_key'
    with db_secret.open('rb') as f: DB_SECRET = f.read()

else:
    IMQ_SECRET = os.environ['IMQ_SECRET']
    OMQ_SECRET = os.environ['OMQ_SECRET']
    DB_SECRET = os.environ['DB_SECRET']


# Logs
LOG_LIMIT = 1000
LOG_EVENTS_FILE = PROJECT_DIR / 'logs' / 'events.log'
LOG_EXCEPTIONS_FILE = PROJECT_DIR / 'logs' / 'exceptions.log'
LOG_WERKZEUG_FILE = PROJECT_DIR / 'logs' / 'werkzeug.log'
LOG_TELEBOT_FILE = PROJECT_DIR / 'logs' / 'pyTelegramBotAPI.log'


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
