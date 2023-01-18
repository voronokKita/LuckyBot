""" Responder. Process commands. """
import sys

import logging
from logs import console, event
logger = logging.getLogger(__name__)


class Respond:
    def delete_user(self, tg_uid, start_cmd=False):
        pass

    def delete_notes(self, tg_uid, notes:list):
        pass

    def send_message(self, tg_uid, text):
        pass

    def send_list(self, tg_uid):
        pass
