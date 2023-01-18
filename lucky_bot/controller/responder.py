""" Responder. Process commands.

Integrated with the main db, and with Sender's Output Messages Queue.
"""
from lucky_bot.helpers.signals import INCOMING_MESSAGE
from lucky_bot import MainDB
from lucky_bot.sender import OutputQueue

import logging
from logs import console, event
logger = logging.getLogger(__name__)


class Respond:
    @staticmethod
    def send_message(tg_uid, text):
        OutputQueue.add_message(tg_uid, text, 1)
        if not INCOMING_MESSAGE.is_set():
            INCOMING_MESSAGE.set()

    @staticmethod
    def delete_user(tg_uid, start_cmd=False):
        if start_cmd is False:
            event.info('internal command: delete user')
            console('internal command: delete user')
        MainDB.delete_user(tg_uid)

    def delete_notes(self, tg_uid, notes:list):
        errors = ''
        for note in notes:
            if MainDB.delete_user_note(tg_uid, note) is False:
                errors += f'Note #{note} - fail to delete.\n'
        if errors:
            self.send_message(tg_uid, errors)
        else:
            self.send_message(tg_uid, 'Deleted.')

    def send_list(self, tg_uid):
        result = MainDB.get_user_notes(tg_uid)
        if not result:
            self.send_message(tg_uid, 'Nothing.')

        message = 'Your notes:\n'
        for note_obj in result:
            t = note_obj.text[:30].strip()
            if len(note_obj.text) > 30:
                t += '...'
            message += f'* №{note_obj.number} :: "{t}"\n\n'

        self.send_message(tg_uid, message)

    def send_note(self, tg_uid, note_num):
        result = MainDB.get_user_note(tg_uid, note_num)
        if not result:
            self.send_message(tg_uid, 'Number not found. Check the note number by calling /list.')
        else:
            self.send_message(tg_uid, result.text)
