from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED, EXIT_SIGNAL,
    NEW_MESSAGE_TO_SEND,
)
from lucky_bot.helpers.constants import SenderException
from lucky_bot.models.output_mq import OutputQueue
from lucky_bot.bot_config import send_message

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


class SenderThread(ThreadTemplate):
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def __str__(self):
        return 'sender thread'

    def body(self):
        try:
            self._process_all_messages()
            self._set_the_signal()
            self._test_exception()

            while True:
                if NEW_MESSAGE_TO_SEND.wait():
                    pass
                if EXIT_SIGNAL.is_set():
                    break
                self._process_all_messages()
                NEW_MESSAGE_TO_SEND.clear()
                self._test_sender_cycle()

        except Exception as exc:
            raise SenderException(exc)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.set()
        super().merge()

    def _process_all_messages(self):
        while True:
            msg_obj = OutputQueue.get_first_message()
            if msg_obj:
                self._process_a_message(msg_obj)
            else:
                break

    @staticmethod
    def _process_a_message(msg_obj):
        result = send_message(msg_obj.destination, msg_obj.text)
        if result is True:
            OutputQueue.delete_message(msg_obj)
            return
        # TODO if False

    def _test_sender_cycle(self):
        pass

