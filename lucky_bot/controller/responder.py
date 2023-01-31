"""
Controller's command responder. Process commands.
It makes queries to the main database and sends messages to the output messages queue.

Exceptions go through:
    DatabaseException
    OMQException
"""
from lucky_bot.helpers.constants import DatabaseException
from lucky_bot.helpers.signals import NEW_MESSAGE_TO_SEND
from lucky_bot import MainDB
from lucky_bot.sender import OutputQueue

import logging
logger = logging.getLogger(__name__)
from logs import Log


class Respond:
    def send_message(self, tg_uid, text):
        """ Pass message to the sender module. """
        OutputQueue.add_message(tg_uid, text)
        if not NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.set()

    def add_user(self, tg_uid):
        MainDB.add_user(tg_uid)

    def delete_user(self, tg_uid, start_cmd=False):
        if start_cmd is False:
            Log.info("controller's responder: delete a user")
        MainDB.delete_user(tg_uid)

    def delete_notes(self, tg_uid, notes:list):
        message = ''
        for note in notes:
            message = self._delete_note(tg_uid, note, message)

        if message:
            self.send_message(tg_uid, message)

    def _delete_note(self, tg_uid, note, message):
        """ Propagates: DatabaseException """
        try:
            if MainDB.delete_user_note(tg_uid, note) is False:
                message += f'Note #`{note}` - not found\n'
            else:
                message += f'Note #`{note}` - deleted\n'
            return message

        except DatabaseException as exc:
            # Send message, if any, before an exception propagation.
            if message:
                message += 'Some internal Error...\n'
                self.send_message(tg_uid, message)
            raise exc

    def send_list(self, tg_uid):
        result = MainDB.get_user_notes(tg_uid)
        if not result:
            self.send_message(tg_uid, 'Nothing.')
            return

        message = 'Your notes:\n'
        for note_obj in result:
            t = note_obj.text[:30].strip()
            if len(note_obj.text) > 30:
                t += '...'
            message += f'* №`{note_obj.number}` :: "{t}"\n\n'

        self.send_message(tg_uid, message)

    def send_note(self, tg_uid, note_num):
        result = MainDB.get_user_note(tg_uid, note_num)
        if not result:
            self.send_message(tg_uid, 'Number not found. Check the note number by calling /list.')
        else:
            self.send_message(tg_uid, result.text)
