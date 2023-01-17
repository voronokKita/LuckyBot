""" Parser.
Processes data and inserts it into the main database.
"""
import sys

import logging
from logs import console, event
logger = logging.getLogger(__name__)


def parse_note_and_insert(uid, text) -> str:
    return 'Done.'


def parse_note_and_update(uid, text, note_num) -> str:
    return 'Done.'
