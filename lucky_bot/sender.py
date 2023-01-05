from lucky_bot.helpers.misc import ThreadTemplate
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED, EXIT_SIGNAL,
    NEW_MESSAGE_TO_SEND,
)
from lucky_bot.helpers.constants import (
    SenderException, DispatcherWrongToken, DispatcherNoAccess,
    DispatcherTimeout, DispatcherUndefinedExc, DispatcherException,
    StopTheSenderGently,
)
from lucky_bot.models.output_mq import OutputQueue
from lucky_bot import dispatcher

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

        except StopTheSenderGently:
            EXIT_SIGNAL.set()
        except DispatcherException as exc:
            raise exc
        except Exception as exc:
            event.error('sender: exception')
            console('sender: exception')
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
                self._process_a_delivery(msg_obj)
            else:
                break

    @staticmethod
    def _process_a_delivery(msg_obj):
        try:
            dispatcher.send_message(msg_obj.destination, msg_obj.text)

        except DispatcherException as exc:
            event.error('sender: stopping because of dispatcher exception')
            console('sender: stopping because of dispatcher exception')
            raise exc

        except DispatcherWrongToken:
            event.error('sender: stopping because of api error')
            console('sender: stopping because of api error')
            raise StopTheSenderGently

        except DispatcherTimeout:
            event.warning('sender: stopping because of tg timeout')
            console('sender: stopping because of tg timeout')
            raise StopTheSenderGently

        except DispatcherUndefinedExc:
            msg = 'sender: deleting the broken message; delete the uid manually if the exception persists'
            event.warning(msg)
            console(msg)
            OutputQueue.delete_message(msg_obj)

        except DispatcherNoAccess:
            event.warning('sender: deleting the inaccessible uid')
            console('sender: deleting the inaccessible uid')
            OutputQueue.delete_message(msg_obj)
            # TODO delete a uid request

        else:
            OutputQueue.delete_message(msg_obj)

    def _test_sender_cycle(self):
        pass

