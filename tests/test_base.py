""" python -m unittest tests.test_base """
import sys
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestProjectBase(unittest.TestCase):
    ''' Main files and structure. '''
    def testit(self):
        package_dir = BASE_DIR / 'lucky_bot'
        files = [
            BASE_DIR / '.gitignore',
            BASE_DIR / 'main.py',
            BASE_DIR / 'Pipfile',
            BASE_DIR / 'README.md',
            BASE_DIR / 'design.png',

            package_dir / 'receiver' / 'webhook.py',
            package_dir / 'receiver' / 'input_message_queue.sqlite3',
            package_dir / 'receiver' / 'input_controller.py',

            package_dir / 'parser' / 'parser.py',
            package_dir / 'controller' / 'telegram_controller.py',
            package_dir / 'updater' / 'updater.py',

            package_dir / 'sender' / 'sender.py',
            package_dir / 'sender' / 'output_message_queue.sqlite3',
        ]
        for f in files:
            self.assertTrue(f.exists(), msg=f)

        import flask
        import pyngrok
        import sqlalchemy
        self.assertIn('3.11', sys.version)

        import main
        from lucky_bot.receiver import webhook
        from lucky_bot.receiver import input_controller
        from lucky_bot.parser import parser
        from lucky_bot.data import models
        from lucky_bot.controller import telegram_controller
        from lucky_bot.updater import updater
        from lucky_bot.sender import sender


if __name__ == '__main__':
    if str(BASE_DIR) not in sys.path:
        sys.path.append(str(BASE_DIR))
    unittest.main()
