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
    def send_message(uid: str | int | bytes, message: str | bytes,
                     markup=False, encrypted=False):
        """ Pass message to the sender module. """
        OutputQueue.add_message(uid, message, markup=markup, encrypted=encrypted)
        NEW_MESSAGE_TO_SEND.set() if not NEW_MESSAGE_TO_SEND.is_set() else None

    def add_user(self, uid: str | int):
        MainDB.add_user(uid)

    def delete_user(self, uid: str | int, start_cmd=False):
        if start_cmd is False:
            Log.info("controller's responder: delete a user")
        MainDB.delete_user(uid)

    def send_list(self, uid: str | int):
        if not (result := MainDB.get_user_notes(uid)):
            self.send_message(uid, 'Nothing.')
            return

        message = 'Your notes:\n'
        for note_obj in result:
            decrypted_text = decrypt(note_obj.text)

            lines = decrypted_text[:40].splitlines()
            text1 = '_'.join([l for l in lines if l])
            text2 = text1[:30].strip()
            if len(text1) > 30:
                text2 += '...'

            message += f'* №{note_obj.number} :: "{text2}"\n\n'

        self.send_message(uid, message)

    def send_note(self, uid: str | int, note_num: str | int):
        if not (result := MainDB.get_user_note(uid, note_num)):
            msg = 'Number not found. Check the note number by calling /list.'
            self.send_message(uid, msg)
        else:
            self.send_message(encrypt(uid), result.text, markup=True, encrypted=True)

    def delete_notes(self, uid: str | int, notes: list):
        """ Propagates: DatabaseException """
        tg_id_hash = make_hash(uid)
        message = ''
        try:
            for note_num in notes:
                message += self._delete_note(tg_id_hash, note_num)

            self.send_message(uid, message) if message else None

        except DatabaseException as exc:
            # Send message, if any, before an exception propagation.
            if message:
                message += 'Some internal Error...\n'
                self.send_message(uid, message)
            raise exc

    @classmethod
    def _delete_note(cls, tg_id_hash: str, note_num: str | int):
        if MainDB.delete_user_note(tg_id_hash, note_num) is False:
            return f'Note #{note_num} - not found\n'
        else:
            return f'Note #{note_num} - deleted\n'

    def admin_total_errors(self):
        with ERRORS_TOTAL.open('r') as f: errors_total = f.read().strip()

        self.send_message(MASTER, f'Errors count: {errors_total}')

        if int(errors_total) > 0:
            with ERRORS_TOTAL.open('w') as f: f.write('0')

    def admin_count_users(self):
        if not (result := MainDB.count_users()):
            self.send_message(MASTER, 'There is no one here.')
        else:
            users, notes = result
            self.send_message(MASTER, f'Users: {users}, notes total: {notes}.')

    def admin_mail_users(self, msg: str):
        for user in MainDB.get_all_users():
            self.send_message(user.c_id, encrypt(f'Notification:\n{msg}'), encrypted=True)
