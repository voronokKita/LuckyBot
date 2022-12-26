""" python -m unittest tests.test_base """
import sys
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestProjectBase(unittest.TestCase):
    ''' Base files, structure and syntax. '''
    def testit(self):
        package_dir = BASE_DIR / 'lucky_bot'
        files = [
            BASE_DIR / '.gitignore',
            BASE_DIR / 'main.py',
            BASE_DIR / 'Pipfile',
            BASE_DIR / 'README.md',
            BASE_DIR / 'design.png',

            BASE_DIR / 'data' / 'data.sqlite3',
            BASE_DIR / 'data' / 'input_message_queue.sqlite3',
            BASE_DIR / 'data' / 'output_message_queue.sqlite3',

            package_dir / 'helpers' / 'signals.py',
            package_dir / 'helpers' / 'constants.py',

            package_dir / 'webhook.py',
            package_dir / 'input_controller.py',
            package_dir / 'parser.py',
            package_dir / 'telegram_controller.py',
            package_dir / 'updater.py',
            package_dir / 'sender.py',
        ]
        for f in files:
            self.assertTrue(f.exists(), msg=f)

        self.assertIn('3.11', sys.version)
        import flask
        import pyngrok
        import sqlalchemy

        from lucky_bot.helpers import signals
        from lucky_bot.helpers import constants

        from lucky_bot import webhook
        from lucky_bot import input_controller
        from lucky_bot import parser
        from lucky_bot import models
        from lucky_bot import telegram_controller
        from lucky_bot import updater
        from lucky_bot import sender

        import main
