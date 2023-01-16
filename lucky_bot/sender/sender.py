""" Sender thread.

Integrated with the Output Message Queue and Dispatcher.
"""
from lucky_bot.helpers.constants import (
    SenderException, StopTheSenderGently,
    DispatcherWrongToken, DispatcherNoAccess, DispatcherTimeout,
    DispatcherUndefinedExc, DispatcherException,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    NEW_MESSAGE_TO_SEND, EXIT_SIGNAL,
)
from lucky_bot.helpers.misc import ThreadTemplate

from lucky_bot.sender import OutputQueue
from lucky_bot.sender import dispatcher

import logging
from logs import console, event
logger = logging.getLogger(__name__)


class SenderThread(ThreadTemplate):
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def __str__(self):
        return 'sender thread'

    def body(self):
        """
        Description:
            0. Check the Output Message Queue; Dispatch any messages;
            1. Clear NEW_MESSAGE_TO_SEND, is set;
            2. Set the SENDER_IS_RUNNING signal;
            3. Loop and wait for the NEW_MESSAGE_TO_SEND signal.

            To break the sender from the loop and stop its work,
            the NEW_MESSAGE_TO_SEND signal must be set after the EXIT_SIGNAL.

        Raises:
            DispatcherException: propagation
            SenderException
        """
        try:
            self._process_all_messages()
            if NEW_MESSAGE_TO_SEND.is_set():
                NEW_MESSAGE_TO_SEND.clear()
            self._set_the_signal()
            self._test_exception_after_signal()

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
                OutputQueue.delete_message(msg_obj)
            else:
                break

    @staticmethod
    def _process_a_delivery(msg_obj):
        """ Calls Dispatcher and handles its exceptions.

        Raises:
            DispatcherException: propagation
            StopTheSenderGently
        """

        try:
            dispatcher.send_message(msg_obj.destination, msg_obj.text)

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

        except DispatcherNoAccess:
            event.info('sender: deleting the inaccessible uid')
            console('sender: deleting the inaccessible uid')
            # TODO delete a uid request

        except (DispatcherException, Exception) as exc:
            event.error('sender: stopping because of dispatcher exception')
            console('sender: stopping because of dispatcher exception')
            if isinstance(exc, DispatcherException):
                raise exc
            else:
                raise DispatcherException(exc)

    @staticmethod
    def _test_sender_cycle():
        pass
