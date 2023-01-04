""" python -m unittest tests.test_base """
import sys
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestProjectBase(unittest.TestCase):
    ''' Base files, structure and syntax. '''
    def test_project_base(self):
        package_dir = BASE_DIR / 'lucky_bot'
        files = [
            BASE_DIR / '.gitignore',
            BASE_DIR / 'main.py',
            BASE_DIR / 'Pipfile',
            BASE_DIR / 'README.md',
            BASE_DIR / 'design.png',
            BASE_DIR / 'resources' / '.tgapi',
            BASE_DIR / 'resources' / '.webhook_secret_token',

            package_dir / 'models' / 'database.py',
            package_dir / 'models' / 'input_mq.py',
            package_dir / 'models' / 'output_mq.py',

            package_dir / 'helpers' / 'signals.py',
            package_dir / 'helpers' / 'constants.py',
            package_dir / 'helpers' / 'misc.py',

            package_dir / 'webhook.py',
            package_dir / 'flask_config.py',
            package_dir / 'bot_config.py',
            package_dir / 'controller.py',
            package_dir / 'parser.py',
            package_dir / 'responder.py',
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
        from lucky_bot.helpers import misc

        from lucky_bot.models import database
        from lucky_bot.models import input_mq
        from lucky_bot.models import output_mq

        from lucky_bot import webhook
        from lucky_bot import flask_config
        from lucky_bot import bot_config
        from lucky_bot import controller
        from lucky_bot import parser
        from lucky_bot import responder
        from lucky_bot import updater
        from lucky_bot import sender
        import main

        #! Important things to be mocked
        from lucky_bot.webhook import ngrok
        from lucky_bot.webhook import TeleBot
        from lucky_bot.webhook import WebhookThread
        self.assertTrue(hasattr(WebhookThread, '_make_tunnel'))
        self.assertTrue(hasattr(WebhookThread, '_set_webhook'))
        self.assertTrue(hasattr(WebhookThread, '_make_server'))
        self.assertTrue(hasattr(WebhookThread, '_start_server'))
        self.assertTrue(hasattr(WebhookThread, '_remove_webhook'))
        self.assertTrue(hasattr(WebhookThread, '_close_tunnel'))
        from lucky_bot.flask_config import InputQueue

        from lucky_bot.sender import send_message
        from lucky_bot.sender import OutputQueue
        from lucky_bot.models.output_mq import OutputQueue
        self.assertTrue(hasattr(OutputQueue, 'get_first_message'))
        from lucky_bot.sender import SenderThread
        self.assertTrue(hasattr(SenderThread, '_process_all_messages'))
