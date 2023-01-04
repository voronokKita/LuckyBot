import os
import re
import sys
import pathlib


PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

if [arg for arg in sys.argv if 'test' in arg]:
    TESTING = True
else:
    TESTING = False

if TESTING:
    # NOTE: :memory: db is not working, because
    # a werkzeug server - make_server(), - is running in another process,
    # i.e. in another memory area.
    DB_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_imq.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'tests' / 'fixtures' / 'test_omq.sqlite3'
else:
    DB_FILE = PROJECT_DIR / 'data' / 'data.sqlite3'
    INPUT_MQ_FILE = PROJECT_DIR / 'data' / 'input_message_queue.sqlite3'
    OUTPUT_MQ_FILE = PROJECT_DIR / 'data' / 'output_message_queue.sqlite3'

# Web settings
REPLIT = False
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
TREAD_RUNNING_TIMEOUT = 10

# Exceptions
class TestException(Exception):
    ''' For testing purposes. '''

class MainException(Exception):
    ''' For a main.py '''

class WebhookWrongRequest(Exception):
    ''' Wrong request format. '''

class ThreadException(Exception):
    ''' For the threads, except main. '''

class WebhookException(ThreadException):
    ''' Something wrong in the webhook thread. '''

class FlaskException(ThreadException):
    ''' Something wrong in the flask app. '''

class SenderException(ThreadException):
    ''' Something wrong in the sender thread. '''
