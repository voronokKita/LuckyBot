"""
Controller's data parser.
Processes data and inserts it into the main database.
Right now it's omitted and works just like an interface.

Exceptions go through: DatabaseException
"""
from lucky_bot import MainDB

import logging
logger = logging.getLogger(__name__)


def parse_note_and_insert(uid: str | int, text: str) -> str:
    if MainDB.add_note(uid, text) is True:
        return 'Saved.'
    else:
        return ''


def parse_note_and_update(uid: str | int, text: str, note_num: str | int) -> str:
    if MainDB.update_user_note(uid, note_num, text) is True:
        return 'Updated.'
    else:
        return 'Error: wrong note number.'
