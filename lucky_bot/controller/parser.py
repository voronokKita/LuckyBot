""" Parser.
Processes data and inserts it into the main database.
Right now it's omitted and works just like an interface.
"""
from lucky_bot import MainDB

import logging
logger = logging.getLogger(__name__)


def parse_note_and_insert(uid, text) -> str:
    if MainDB.add_note(uid, text) is True:
        return 'Saved.'
    else:
        return 'Error: check text format and try again.'


def parse_note_and_update(uid, text, note_num) -> str:
    if MainDB.update_user_note(uid, note_num, text) is True:
        return 'Updated.'
    else:
        return 'Error: wrong note number or text format; check for errors and try again.'
