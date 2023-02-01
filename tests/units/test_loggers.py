""" python -m unittest -v tests.units.test_loggers
This test should not be run together with others. """
import unittest
from unittest.mock import patch

import logging
import logging.config as logging_config

from lucky_bot.helpers.constants import PROJECT_DIR, TestException

from logs.config import normal_logger, dummy_logger, clear_old_logs

fixtures = PROJECT_DIR / 'tests' / 'fixtures'
assert fixtures.exists() is True
LOG_EXCEPTIONS_FILE = fixtures / 'test_exceptions.log'
LOG_WERKZEUG_FILE = fixtures / 'test_werkzeug.log'
LOG_TELEBOT_FILE = fixtures / 'test_pyTelegramBotAPI.log'
LOG_EVENTS_FILE = fixtures / 'test_events.log'


@patch('logs.config.LOG_EVENTS_FILE', LOG_EVENTS_FILE)
@patch('logs.config.LOG_TELEBOT_FILE', LOG_TELEBOT_FILE)
@patch('logs.config.LOG_WERKZEUG_FILE', LOG_WERKZEUG_FILE)
@patch('logs.config.LOG_EXCEPTIONS_FILE', LOG_EXCEPTIONS_FILE)
@patch('logs.config.TESTING', False)
class TestLogger(unittest.TestCase):
    def tearDown(self):
        LOG_EXCEPTIONS_FILE.unlink() if LOG_EXCEPTIONS_FILE.exists() else None
        LOG_WERKZEUG_FILE.unlink() if LOG_WERKZEUG_FILE.exists() else None
        LOG_TELEBOT_FILE.unlink() if LOG_TELEBOT_FILE.exists() else None
        LOG_EVENTS_FILE.unlink() if LOG_EVENTS_FILE.exists() else None

    def logsSearchFor(self, msg, default=False, werkzeug=False,
                      telebot=False, events=False):
        logs = {
            LOG_EXCEPTIONS_FILE: default,
            LOG_WERKZEUG_FILE: werkzeug,
            LOG_TELEBOT_FILE: telebot,
            LOG_EVENTS_FILE: events,
        }
        for path, search in logs.items():
            with path.open('r') as f:
                log_text = f.read().strip()
                if search:
                    self.assertIn(msg, log_text)
                else:
                    self.assertEqual(log_text, '')

    def test_default_filter(self):
        config = normal_logger()
        logging_config.dictConfig(config)
        logger = logging.getLogger('test_logger')

        try:
            raise TestException('default exception')
        except TestException:
            print('\n~~~~~~~~terminal~~~~~~~~')
            logger.exception('test default exception')
            print('~~~~~~~~~~~~~~~~~~~~~~~~')

        self.assertTrue(LOG_EXCEPTIONS_FILE.exists())
        self.logsSearchFor('default exception', default=True)

    def test_werkzeug_filter(self):
        config = normal_logger()
        logging_config.dictConfig(config)
        logger = logging.getLogger('werkzeug')

        try:
            raise TestException('werkzeug exception')
        except TestException:
            print('\n~~~~~~~~terminal~~~~~~~~')
            logger.exception('test werkzeug exception')
            print('~~~~~~~~~~~~~~~~~~~~~~~~')

        self.assertTrue(LOG_WERKZEUG_FILE.exists())
        self.logsSearchFor('werkzeug exception', werkzeug=True)

    def test_telebot_filter(self):
        config = normal_logger()
        logging_config.dictConfig(config)
        logger = logging.getLogger('TeleBot')

        try:
            raise TestException('telebot exception')
        except TestException:
            print('\n~~~~~~~~terminal~~~~~~~~')
            logger.exception('test telebot exception')
            print('~~~~~~~~~~~~~~~~~~~~~~~~')

        self.assertTrue(LOG_TELEBOT_FILE.exists())
        self.logsSearchFor('telebot exception', telebot=True)

    def test_event_filter(self):
        config = normal_logger()
        logging_config.dictConfig(config)

        event = logging.getLogger('event')
        event.error('some event')

        self.assertTrue(LOG_EVENTS_FILE.exists())
        self.logsSearchFor('some event', events=True)

    def test_debug_filter(self):
        config = normal_logger()
        logging_config.dictConfig(config)

        debug = logging.getLogger('debug')
        debug.error('\n[debug message]')

        self.assertTrue(LOG_EVENTS_FILE.exists())
        # assert all the "file logs" are empty
        self.logsSearchFor('')

    def test_dummy_logger(self):
        config = dummy_logger()
        logging_config.dictConfig(config)

        werkzeug_logger = logging.getLogger('werkzeug')
        telebot_logger = logging.getLogger('TeleBot')
        event = logging.getLogger('event')
        debugger = logging.getLogger('debug')
        logger = logging.getLogger('test_logger')

        try:
            raise TestException('void exception')
        except TestException:
            werkzeug_logger.exception('boom')
            telebot_logger.exception('boom')
            logger.exception('boom')
            event.error('boom')
            debugger.error('boom')

        # assert all the "file logs" are empty
        self.assertFalse(LOG_EXCEPTIONS_FILE.exists())
        self.assertFalse(LOG_WERKZEUG_FILE.exists())
        self.assertFalse(LOG_TELEBOT_FILE.exists())
        self.assertFalse(LOG_EVENTS_FILE.exists())
