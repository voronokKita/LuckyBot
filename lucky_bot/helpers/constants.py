import sys
import pathlib


if 'unittest' in sys.argv or [t for t in sys.argv if 'testsuite' in t]:
    TESTING = True
else:
    TESTING = False

PROJECT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent

LOG_EVENTS_FILE = PROJECT_DIR / 'logs' / 'events.log'
LOG_EXCEPTIONS_FILE = PROJECT_DIR / 'logs' / 'exceptions.log'
LOG_WERKZEUG_FILE = PROJECT_DIR / 'logs' / 'werkzeug.log'
LOG_TELEBOT_FILE = PROJECT_DIR / 'logs' / 'pyTelegramBotAPI.log'

TREAD_RUNNING_TIMEOUT = 10


class TestException(Exception):
    ''' For testing purposes. '''

class MainError(Exception):
    ''' For a main.py '''

class ThreadException(Exception):
    ''' For the threads, except main. '''
