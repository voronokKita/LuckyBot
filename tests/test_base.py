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

            package_dir / 'helpers' / 'signals.py',
            package_dir / 'helpers' / 'constants.py',
            package_dir / 'helpers' / 'misc.py',

            package_dir / 'models' / 'database.py',
            package_dir / 'models' / 'output_mq.py',

            package_dir / 'receiver' / 'input_mq.py',
            package_dir / 'receiver' / 'flask_config.py',
            package_dir / 'receiver' / 'receiver.py',

            package_dir / 'bot_config.py',
            package_dir / 'controller.py',
            package_dir / 'parser.py',
            package_dir / 'responder.py',
            package_dir / 'updater.py',
            package_dir / 'sender.py',
            package_dir / 'dispatcher.py',
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
        from lucky_bot.models import output_mq

        from lucky_bot.receiver import InputQueue
        from lucky_bot.receiver import FLASK_APP
        from lucky_bot import receiver

        from lucky_bot import bot_config
        from lucky_bot import controller
        from lucky_bot import parser
        from lucky_bot import responder
        from lucky_bot import updater
        from lucky_bot import sender
        from lucky_bot import dispatcher
        import main

        from lucky_bot.helpers.constants import REPLIT
        self.assertFalse(REPLIT)

        # threads
        from lucky_bot.sender import SenderThread
        from lucky_bot.updater import UpdaterThread
        from lucky_bot.controller import ControllerThread
        from lucky_bot.receiver import ReceiverThread
        sender_tr = SenderThread()
        updater_tr = UpdaterThread()
        controller_tr = ControllerThread()
        receiver_tr = ReceiverThread()
        self.assertEqual(str(sender_tr), 'sender thread')
        self.assertEqual(str(updater_tr), 'updater thread')
        self.assertEqual(str(controller_tr), 'controller thread')
        self.assertEqual(str(receiver_tr), 'receiver thread')
