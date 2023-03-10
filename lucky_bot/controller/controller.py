import telebot

from lucky_bot.helpers.constants import (
    ControllerException, TelebotHandlerException,
    DatabaseException, OMQException, IMQException, AdminExitSignal,
)
from lucky_bot.helpers.signals import (
    CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED,
    INCOMING_MESSAGE, EXIT_SIGNAL,
)
from lucky_bot.helpers.misc import ThreadTemplate

from lucky_bot import BOT
from lucky_bot.receiver import InputQueue
from lucky_bot.controller import Respond

import logging
logger = logging.getLogger(__name__)
from logs import Log


''' Commands

Internal
/sender delete [tg_uid] -> responder deletes data

TODO FEATURE admin
/admin something
'''

class Controller:
    """ Gets messages from the input message queue and handles them. """
    responder = Respond()

    @classmethod
    def check_new_messages(cls):
        """
        Exceptions go through:
            IMQException
            OMQException
            DatabaseException
            TelebotHandlerException
            AdminExitSignal: propagation
        """
        while True:
            result = InputQueue.get_first_message()
            if not result:
                break

            message_id, data = result
            try:
                cls._process_the_message(data)
                InputQueue.delete_message(message_id)

            except AdminExitSignal as exc:
                InputQueue.delete_message(message_id)
                raise exc

    @classmethod
    def _process_the_message(cls, data: str):
        """
        Calls the responder or the bot processor, depending on message data.

        Raises:
            TelebotHandlerException
            DatabaseException: propagation
            OMQException: propagation
            AdminExitSignal: propagation
        """
        if data.startswith('/'):
            if data.startswith('/sender delete'):
                uid = data.removeprefix('/sender delete ')
                cls.responder.delete_user(uid)
        else:
            try:
                update = telebot.types.Update.de_json(data)
                BOT.process_new_updates([update])

            except AdminExitSignal as exc:
                raise exc
            except (DatabaseException, OMQException) as exc:
                raise exc
            except Exception as exc:
                msg = 'controller: exception in a telebot handler'
                Log.error(msg)
                raise TelebotHandlerException(exc)


class ControllerThread(ThreadTemplate):
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED
    signal_after_exit = INCOMING_MESSAGE
    controller = Controller()

    def __str__(self):
        return 'controller thread'

    def body(self):
        """
        Description:
            0. Check the Input Message Queue, respond or parse any messages;
            1. Clear INCOMING_MESSAGE signal, if set;
            2. Set the CONTROLLER_IS_RUNNING signal;
            3. Loop and wait for the NEW_INCOMING_MESSAGE signal.

            To break the controller from the loop and stop its work,
            the INCOMING_MESSAGE signal must be set after the EXIT_SIGNAL.

        Raises:
            ControllerException
            TelebotHandlerException: propagation
            DatabaseException: propagation
            IMQException: propagation
            OMQException: propagation
        """
        try:
            self.work_before_the_loop()

            while True:
                if INCOMING_MESSAGE.wait(3600):
                    pass

                if EXIT_SIGNAL.is_set():
                    break
                else:
                    self.controller.check_new_messages()
                    INCOMING_MESSAGE.clear()
                    self._test_controller_cycle()

        except AdminExitSignal as exc:
            EXIT_SIGNAL.set()
        except (OMQException, IMQException,
                TelebotHandlerException, DatabaseException) as exc:
            raise exc
        except Exception as exc:
            Log.error('controller: a normal exception')
            raise ControllerException(exc)

    def work_before_the_loop(self):
        self.controller.check_new_messages()
        INCOMING_MESSAGE.clear()
        self._set_the_signal()
        self._test_exception_after_signal()

    @staticmethod
    def _test_controller_cycle():
        pass
