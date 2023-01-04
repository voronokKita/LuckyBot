import logging
import logging.config

from lucky_bot.helpers.constants import (
    TESTING, LOG_EVENTS_FILE, LOG_TELEBOT_FILE,
    LOG_WERKZEUG_FILE, LOG_EXCEPTIONS_FILE, LOG_LIMIT,
)


def get_config():
    class DetailedExceptionFilter(logging.Filter):
        blacklist = {'werkzeug', 'TeleBot', 'event'}
        def filter(self, record):
            return record.name not in self.blacklist

    class WerkzeugFilter(logging.Filter):
        def filter(self, record):
            return record.name == 'werkzeug'

    class TeleBotFilter(logging.Filter):
        def filter(self, record):
            return record.name == 'TeleBot'

    class EventFilter(logging.Filter):
        def filter(self, record):
            return record.name == 'event'

    class ConsoleFilter(logging.Filter):
        blacklist = {'event'}
        def filter(self, record):
            return record.name not in self.blacklist

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            # 'console_debug': {'format': '[DEBUG] {message} [/DEBUG]', 'style': '{'},
            'event_to_file': {'format': '-- {asctime} {levelname} {message}', 'style': '{'},
            'exception_to_file': {
                'format': '\n[{levelname}] {asctime}\n'
                          '[MESSAGE] {message}',
                'style': '{',
            },
        },
        'handlers': {
            # 'console': {
            #     'level': 'INFO',
            #     'class': 'logging.StreamHandler',
            #     'stream': 'ext://sys.stdout',  # default is stderr
            # },
            'console_debug': {
                'level': 'DEBUG',
                # 'formatter': 'console_debug',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'event': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': LOG_EVENTS_FILE,
                'formatter': 'event_to_file',
                'filters': [EventFilter()],
            },
            'detailed_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_EXCEPTIONS_FILE,
                'formatter': 'exception_to_file',
                'filters': [DetailedExceptionFilter()],
            },
            'werkzeug_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': [WerkzeugFilter()],
            },
            'werkzeug_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_WERKZEUG_FILE,
                'formatter': 'exception_to_file',
                'filters': [WerkzeugFilter()],
            },
            'telebot_console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': [TeleBotFilter()],
            },
            'telebot_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_TELEBOT_FILE,
                'formatter': 'exception_to_file',
                'filters': [TeleBotFilter()],
            },
        },
        'loggers': {
            'werkzeug': {
                'handlers': ['werkzeug_console', 'werkzeug_exception'],
                'level': 'INFO',
            },
            'TeleBot': {
                'handlers': ['telebot_console', 'telebot_exception'],
                'level': 'INFO',
            },
            'debug': {
                'handlers': ['console_debug'],
                'level': 'DEBUG',
            },
            'event': {
                'handlers': ['event'],
                'level': 'INFO',
            },
            '': {
                'handlers': ['detailed_exception'],
                'level': 'ERROR',
            },
        }
    }
    return logging_config


def dummy_logger():
    logging_config = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'nullifier': {'level': 'CRITICAL', 'class': 'logging.NullHandler'},
        },
        'loggers': {
            'werkzeug': {'handlers': ['nullifier'], 'level': 'CRITICAL'},
            'TeleBot': {'handlers': ['nullifier'], 'level': 'CRITICAL'},
            'debug': {'handlers': ['nullifier'], 'level': 'CRITICAL'},
            'event': {'handlers': ['nullifier'], 'level': 'CRITICAL'},
            '': {'handlers': ['nullifier'], 'level': 'CRITICAL'},
        }
    }
    return logging_config


if TESTING:
    config = dummy_logger()
else:
    config = get_config()

logging.config.dictConfig(config)

debugger = logging.getLogger('debug')
event = logging.getLogger('event')
werkzeug_logger = logging.getLogger('werkzeug')
telebot_logger = logging.getLogger('TeleBot')


def console(msg):
    if TESTING:
        return
    if not isinstance(msg, str):
        msg = str(msg)
    debugger.debug(msg)


def clear_old_logs():
    if TESTING:
        return

    files = [LOG_EVENTS_FILE, LOG_TELEBOT_FILE,
             LOG_WERKZEUG_FILE, LOG_EXCEPTIONS_FILE]

    for logfile in files:
        limit = False
        lines = None
        with logfile.open('r') as f:
            for count, line in enumerate(f):
                pass
            if count > LOG_LIMIT:
                limit = True
                f.seek(0)
                lines = f.readlines()

        if not limit:
            continue

        with logfile.open('w') as f:
            f.write('--------- old lines has ben removed ---------\n')
            lines_to_save = count - LOG_LIMIT // 2
            f.writelines(lines[lines_to_save:])
