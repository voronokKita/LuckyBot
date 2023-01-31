""" Telegram messaging Dispatcher.
It sends messages to Telegram through the telebot and sorts possible exceptions.
"""
import time

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import (
    TG_WRONG_TOKEN, TG_UID_NOT_FOUND,
    TG_BOT_BLOCKED, TG_BOT_TIMEOUT,

    DispatcherWrongToken, DispatcherNoAccess, DispatcherTimeout,
    DispatcherUndefinedExc, OutputDispatcherException,
)
from lucky_bot import BOT

import logging
logger = logging.getLogger(__name__)
from logs import Log


def send_message(uid: int, text: str, file=None):
    """
    Send a message to Telegram and handle possible exception.

    Raises:
        OutputDispatcherException
        DispatcherWrongToken
        DispatcherNoAccess
        DispatcherTimeout
        DispatcherUndefinedExc
    """
    attempt = 0
    while attempt < 3:
        attempt += 1
        try:
            BOT.send_message(uid, text)
            break

        except ApiTelegramException as aexc:
            if TG_WRONG_TOKEN.search(aexc.description):
                msg = 'output dispatcher: wrong telegram token'
                logger.exception(msg)
                Log.error(msg)
                raise DispatcherWrongToken(msg)

            elif TG_UID_NOT_FOUND.search(aexc.description):
                msg = 'output dispatcher: uid not found'
                Log.warning(msg)
                raise DispatcherNoAccess(msg)

            elif TG_BOT_BLOCKED.search(aexc.description):
                msg = 'output dispatcher: bot blocked'
                Log.warning(msg)
                raise DispatcherNoAccess(msg)

            elif TG_BOT_TIMEOUT.search(aexc.description):
                if attempt < 3:
                    time.sleep(10)
                    continue
                else:
                    msg = 'output dispatcher: telegram timeout'
                    Log.warning(msg)
                    raise DispatcherTimeout(msg)

            else:
                if attempt < 3:
                    time.sleep(1)
                    continue
                else:
                    msg = 'output dispatcher: undefined ApiTelegramException'
                    Log.warning(msg)
                    raise DispatcherUndefinedExc(msg)

        except Exception as exception:
            msg = 'output dispatcher: normal exception'
            logger.exception(msg)
            Log.error(msg)
            raise OutputDispatcherException(exception)
