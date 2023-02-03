"""
Controller's command responder. Process commands.
It makes queries to the main database and sends messages to the output messages queue.

Exceptions go through:
    DatabaseException
    OMQException
"""
from lucky_bot.helpers.constants import DatabaseException, ERRORS_TOTAL, MASTER
from lucky_bot.helpers.misc import encrypt, decrypt, make_hash
from lucky_bot.helpers.signals import NEW_MESSAGE_TO_SEND
from lucky_bot import MainDB
from lucky_bot.sender import OutputQueue

import logging
logger = logging.getLogger(__name__)
from logs import Log


class Respond:
    @staticmethod
    def send_message(uid: str | int | bytes, message: str | bytes, encrypted=False):
        """ Pass message to the sender module. """
        if encrypted:
            OutputQueue.add_message(uid, message, encrypted=True)
        else:
            OutputQueue.add_message(uid, message)
        if not NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.set()

    def add_user(self, uid: str | int):
        MainDB.add_user(uid)

    def delete_user(self, uid: str | int, start_cmd=False):
        if start_cmd is False:
            Log.info("controller's responder: delete a user")
        MainDB.delete_user(uid)

    def send_list(self, uid: str | int):
        result = MainDB.get_user_notes(uid)
        if not result:
            self.send_message(uid, 'Nothing.')
            return

        message = 'Your notes:\n'
        for note_obj in result:
            decrypted_text = decrypt(note_obj.text)
            text = decrypted_text[:30].strip()
            if len(decrypted_text) > 30:
                text += '...'
            message += f'* №`{note_obj.number}` :: "{text}"\n\n'

        self.send_message(uid, message)

    def send_note(self, uid: str | int, note_num: str | int):
        result = MainDB.get_user_note(uid, note_num)
        if not result:
            self.send_message(uid, 'Number not found. Check the note number by calling /list.')
        else:
            self.send_message(encrypt(uid), result.text, encrypted=True)

    def delete_notes(self, uid: str | int, notes: list):
        message = ''
        tg_id_hash = make_hash(uid)
        for note_num in notes:
            message = self._delete_note(uid, tg_id_hash, note_num, message)

        if message:
            self.send_message(uid, message)

    @classmethod
    def _delete_note(cls, uid: str | int, tg_id_hash: str,
                     note_num: str | int, message: str):
        """ Propagates: DatabaseException """
        try:
            if MainDB.delete_user_note(tg_id_hash, note_num) is False:
                message += f'Note #`{note_num}` - not found\n'
            else:
                message += f'Note #`{note_num}` - deleted\n'
            return message

        except DatabaseException as exc:
            # Send message, if any, before an exception propagation.
            if message:
                message += 'Some internal Error...\n'
                cls.send_message(uid, message)
            raise exc

    def admin_total_errors(self):
        with ERRORS_TOTAL.open('r') as f:
            errors_total = f.read().strip()

        self.send_message(MASTER, f'Errors count: {errors_total}')

        if int(errors_total) > 0:
            with ERRORS_TOTAL.open('w') as f: f.write('0')

    def admin_count_users(self):
        result = MainDB.count_users()
        if not result:
            self.send_message(MASTER, 'There is no one here.')
        else:
            users, notes = result
            self.send_message(MASTER, f'Users: {users}, notes total: {notes}.')

    def admin_mail_users(self, msg: str):
        users = MainDB.get_all_users()
        for user in users:
            self.send_message(user.c_id, encrypt(f'Notification:\n{msg}'), encrypted=True)
