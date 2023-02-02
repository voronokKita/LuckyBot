from lucky_bot.helpers.constants import (
    SenderException, StopTheSenderGently, OMQException, IMQException,
    DispatcherWrongToken, DispatcherNoAccess, DispatcherTimeout,
    DispatcherUndefinedExc, OutputDispatcherException,
)
from lucky_bot.helpers.signals import (
    SENDER_IS_RUNNING, SENDER_IS_STOPPED,
    NEW_MESSAGE_TO_SEND, INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.helpers.misc import ThreadTemplate

from lucky_bot.receiver import InputQueue
from lucky_bot.sender import OutputQueue
from lucky_bot.sender import output_dispatcher

import logging
logger = logging.getLogger(__name__)
from logs import Log


class Sender:
    """ Gets messages from the output message queue and passes them to the output dispatcher. """

    @classmethod
    def process_outgoing_messages(cls):
        """
        Exceptions go through:
            OutputDispatcherException
            StopTheSenderGently
            OMQException
            IMQException
        """
        while True:
            result = OutputQueue.get_first_message()
            if result:
                message_id, destination, message = result
                cls._handle_a_delivery(destination, message)
                OutputQueue.delete_message(message_id)
            else:
                break

    @staticmethod
    def _handle_a_delivery(destination, message):
        """
        Calls the dispatcher and handles its exceptions.
        Sends /delete commands to the input message queue.

        Exceptions go through:
            IMQException

        Raises:
            StopTheSenderGently
            OutputDispatcherException: propagation
        """
        try:
            output_dispatcher.send_message(destination, message)

        except DispatcherWrongToken:
            Log.error('sender: stopping because of api error')
            raise StopTheSenderGently

        except DispatcherTimeout:
            Log.warning('sender: stopping because of tg timeout')
            raise StopTheSenderGently

        except DispatcherUndefinedExc:
            Log.warning('sender: deleting the broken message; delete the uid manually if the exception persists')

        except DispatcherNoAccess:
            Log.info('sender: deleting the inaccessible uid')
            InputQueue.add_message(f'/sender delete {destination}')
            INCOMING_MESSAGE.set()

        except (OutputDispatcherException, Exception) as exc:
            Log.error('sender: stopping because of dispatcher exception')
            if isinstance(exc, OutputDispatcherException):
                raise exc
            else:
                raise OutputDispatcherException(exc)


class SenderThread(ThreadTemplate):
    is_running_signal = SENDER_IS_RUNNING
    is_stopped_signal = SENDER_IS_STOPPED

    def __str__(self):
        return 'sender thread'

    def body(self):
        """
        Description:
            0. Dispatch any messages;
            1. Clear NEW_MESSAGE_TO_SEND signal, if set;
            2. Set the SENDER_IS_RUNNING signal;
            3. Loop and wait for the NEW_MESSAGE_TO_SEND signal.

            To break the sender from the loop and stop its work,
            the NEW_MESSAGE_TO_SEND signal must be set after the EXIT_SIGNAL.

        Raises:
            SenderException
            DispatcherException: propagation
            OMQException: propagation
            IMQException: propagation
        """
        try:
            Sender.process_outgoing_messages()

            if NEW_MESSAGE_TO_SEND.is_set():
                NEW_MESSAGE_TO_SEND.clear()
            self._set_the_signal()
            self._test_exception_after_signal()

            while True:
                if NEW_MESSAGE_TO_SEND.wait(3600):
                    pass
                if EXIT_SIGNAL.is_set():
                    break
                else:
                    Sender.process_outgoing_messages()

                    if NEW_MESSAGE_TO_SEND.is_set():
                        NEW_MESSAGE_TO_SEND.clear()
                    self._test_sender_cycle()

        except StopTheSenderGently:
            EXIT_SIGNAL.set()
        except (OutputDispatcherException, OMQException, IMQException) as exc:
            raise exc
        except Exception as exc:
            Log.error('sender: a normal exception')
            raise SenderException(exc)

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        if not NEW_MESSAGE_TO_SEND.is_set():
            NEW_MESSAGE_TO_SEND.set()
        super().merge()

    @staticmethod
    def _test_sender_cycle():
        pass
