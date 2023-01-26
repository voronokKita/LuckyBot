""" Updater notifications dispatcher. """
import random
from time import time
from lucky_bot.sender import OutputQueue
from lucky_bot import MainDB

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


def clear_all_users_flags(current_time):
    if current_time.before_the_first_update:
        MainDB.clear_all_users_flags()


def send_messages(current_time):
    if not current_time.before_the_first_update:
        notifications_dispatcher(current_time)


def notifications_dispatcher(current_time):
    """
    0. Take all the users that have at least 1 note;
    1. Check that the user hasn't yet received a message for the current time;
    3. Get user's notifications for the updater and select one random message;
    4. Pass this message to the Output Message Queue;
    5. Set the user flag for the current time.
    """
    users = MainDB.get_users_with_notes()
    if not users:
        return

    for user in users:
        if not is_waiting_for_update(user, current_time):
            continue

        notes = MainDB.get_notifications_for_the_updater(user.tg_id)
        if not notes:
            msg = f"updater: got a user that don't have any notes to send, id #{user.id}"
            console(msg)
            event.warning(msg)
            continue

        note = random.choice(notes)
        OutputQueue.add_message(user.tg_id, note.text, int(time()))
        set_update_flag(user.tg_id, current_time)


def is_waiting_for_update(user, current_time):
    if current_time.first_update and not user.got_first_update:
        return True
    elif current_time.second_update and not user.got_second_update:
        return True
    else:
        return False


def set_update_flag(uid, current_time):
    if current_time.first_update:
        MainDB.set_user_flag(uid, 'first update')
    elif current_time.second_update:
        MainDB.set_user_flag(uid, 'second update')
