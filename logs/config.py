""" Logging configuration. """
import logging
import logging.config as logs_config

from lucky_bot.helpers.constants import (
    TESTING, LOG_EVENTS_FILE, LOG_TELEBOT_FILE,
    LOG_WERKZEUG_FILE, LOG_EXCEPTIONS_FILE, LOG_LIMIT,
)


class WerkzeugFilter(logging.Filter):
    def filter(self, record):
        return record.name == 'werkzeug'


class TeleBotFilter(logging.Filter):
    def filter(self, record):
        return record.name == 'TeleBot'


class EventFilter(logging.Filter):
    def filter(self, record):
        return record.name == 'event'


class DefaultExceptionFilter(logging.Filter):
    blacklist = {'werkzeug', 'TeleBot', 'event', 'debug'}
    def filter(self, record):
        return record.name not in self.blacklist


class ConsoleFilter(logging.Filter):
    blacklist = {'event'}
    def filter(self, record):
        return record.name not in self.blacklist


def normal_logger():
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'werkzeug_filter': {'()': WerkzeugFilter},
            'telebot_filter': {'()': TeleBotFilter},
            'event_filter': {'()': EventFilter},
            'default_exception_filter': {'()': DefaultExceptionFilter},
        },
        'formatters': {
            'event_to_file': {
                'format': '-- {asctime} {levelname} :: {message}',
                'style': '{'
            },
            'exception_to_file': {
                'format': '\n[{levelname}] {asctime}\n'
                          '[MESSAGE] {message}',
                'style': '{',
            },
        },
        'handlers': {
            'werkzeug_console': {
                'level': 'INFO',  # internal notifications
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': ['werkzeug_filter'],
            },
            'werkzeug_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_WERKZEUG_FILE,
                'formatter': 'exception_to_file',
                'filters': ['werkzeug_filter'],
            },

            'telebot_console': {
                'level': 'INFO',  # internal notifications
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': ['telebot_filter'],
            },
            'telebot_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_TELEBOT_FILE,
                'formatter': 'exception_to_file',
                'filters': ['telebot_filter'],
            },

            'console_debug': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },

            'event': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': LOG_EVENTS_FILE,
                'formatter': 'event_to_file',
                'filters': ['event_filter'],
            },

            'default_console': {
                'level': 'ERROR',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'filters': ['default_exception_filter'],
            },
            'default_exception': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': LOG_EXCEPTIONS_FILE,
                'formatter': 'exception_to_file',
                'filters': ['default_exception_filter'],
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
                'handlers': ['default_console', 'default_exception'],
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
    config = normal_logger()

logs_config.dictConfig(config)

debugger = logging.getLogger('debug')
event = logging.getLogger('event')
werkzeug_logger = logging.getLogger('werkzeug')
telebot_logger = logging.getLogger('TeleBot')
logger = logging.getLogger(__name__)


class Log:
    @staticmethod
    def _console_print(msg):
        debugger.debug(msg)

    @classmethod
    def _event(cls, mode, msg, console):
        """ Bottleneck. """
        if TESTING:
            return

        if console:
            cls._console_print(msg)

        if not mode:
            pass
        elif mode == 'info':
            event.info(msg)
        elif mode == 'warning':
            event.warning(msg)
        elif mode == 'error':
            event.error(msg)
        elif mode == 'critical':
            event.critical(msg)

    @classmethod
    def console(cls, msg):
        cls._event('', msg, console=True)

    @classmethod
    def info(cls, msg, console=True):
        cls._event('info', msg, console)

    @classmethod
    def warning(cls, msg, console=True):
        cls._event('warning', msg, console)

    @classmethod
    def error(cls, msg, console=True):
        cls._event('error', msg, console)

    @classmethod
    def critical(cls, msg, console=True):
        cls._event('critical', msg, console)


def clear_old_logs():
    """ Will delete the first rows, if total number of rows in a log file is > LOG_LIMIT. """
    if TESTING:
        return

    files = [LOG_EVENTS_FILE, LOG_TELEBOT_FILE,
             LOG_WERKZEUG_FILE, LOG_EXCEPTIONS_FILE]

    for logfile in files:
        limit = False
        old_lines = []
        with logfile.open('r') as f:
            count = 0
            for count, line in enumerate(f):
                pass
            if count > LOG_LIMIT:
                limit = True
                f.seek(0)
                old_lines = f.readlines()

        if not limit:
            continue

        with logfile.open('w') as f:
            f.write('--------- old lines has ben removed ---------\n')
            lines_to_save = count - LOG_LIMIT // 2
            f.writelines(
                old_lines[lines_to_save:]
            )
