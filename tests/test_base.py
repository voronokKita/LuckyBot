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

            package_dir / 'database.py',
            package_dir / 'bot_init.py',

            package_dir / 'receiver' / 'input_mq.py',
            package_dir / 'receiver' / 'flask_config.py',
            package_dir / 'receiver' / 'receiver.py',

            package_dir / 'sender' / 'output_mq.py',
            package_dir / 'sender' / 'output_dispatcher.py',
            package_dir / 'sender' / 'sender.py',

            package_dir / 'updater' / 'update_dispatcher.py',
            package_dir / 'updater' / 'updater.py',

            package_dir / 'controller' / 'bot_handlers.py',
            package_dir / 'controller' / 'parser.py',
            package_dir / 'controller' / 'responder.py',
            package_dir / 'controller' / 'controller.py',
            ]
        for f in files:
            self.assertTrue(f.exists(), msg=f)

        self.assertIn('3.11', sys.version)
        import flask
        import pyngrok
        import sqlalchemy

        from lucky_bot.helpers import constants
        from lucky_bot.helpers import signals
        from lucky_bot.helpers import misc

        from lucky_bot import MainDB
        from lucky_bot import BOT

        from lucky_bot.receiver import InputQueue
        from lucky_bot.receiver import FLASK_APP
        from lucky_bot import receiver

        from lucky_bot.sender import OutputQueue
        from lucky_bot.sender import output_dispatcher
        from lucky_bot import sender

        from lucky_bot.updater import update_dispatcher
        from lucky_bot import updater

        from lucky_bot.controller import bot_handlers
        from lucky_bot.controller import parser
        from lucky_bot.controller import responder
        from lucky_bot import controller

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
