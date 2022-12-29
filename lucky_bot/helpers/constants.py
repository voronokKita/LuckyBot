import re
import os
import sys
import pathlib


PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

if [t for t in sys.argv if 'test' in t]:
    TESTING = True
else:
    TESTING = False

# Web settings
REPLIT = False
REPLIT_URL = 'https://LuckyBot.kitavoronok.repl.co'
PORT = 5000
ADDRESS = '0.0.0.0'
WEBHOOK_ENDPOINT = '/webhook'
WEBHOOK_WAS_SET = re.compile('was set|already set')

if REPLIT:
    API = os.environ['API']
else:
    API = PROJECT_DIR / 'resources' / '.api'
    if API.exists():
        with open(API) as f:
            API = f.read().strip()
    else:
        API = input('Enter the telegram API key: ').strip()

# Logs
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

class ThreadException(Exception):
    ''' For the threads, except main. '''
