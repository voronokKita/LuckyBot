""" python -m unittest tests/test_base.py """

import sys
import pathlib
import unittest

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))


class ProjectBase(unittest.TestCase):
    ''' Main files and structure. '''
    def test_base(self):
        files = [
            BASE_DIR / '.gitignore',
            BASE_DIR / 'main.py',
            BASE_DIR / 'Pipfile',
            BASE_DIR / 'README.md',
            BASE_DIR / 'design.png',

            BASE_DIR / 'receiver' / 'webhook.py',
            BASE_DIR / 'receiver' / 'input_message_queue.sqlite3',
            BASE_DIR / 'receiver' / 'input_controller.py',

            BASE_DIR / 'parser' / 'parser.py',
            BASE_DIR / 'controller' / 'telegram_controller.py',
            BASE_DIR / 'updater' / 'updater.py',

            BASE_DIR / 'sender' / 'sender.py',
            BASE_DIR / 'sender' / 'output_message_queue.sqlite3',
        ]
        for f in files:
            self.assertTrue(f.exists(), msg=f)

        import flask
        import pyngrok
        import sqlalchemy
        self.assertIn('3.11', sys.version)

        import main


if __name__ == '__main__':
    unittest.main()
