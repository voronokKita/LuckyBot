""" Telegram messaging Dispatcher. """
import time

from telebot.apihelper import ApiTelegramException

from lucky_bot.helpers.constants import (
    TG_WRONG_TOKEN, TG_UID_NOT_FOUND,
    TG_BOT_BLOCKED, TG_BOT_TIMEOUT,
    DispatcherWrongToken, DispatcherNoAccess, DispatcherTimeout,
    DispatcherUndefinedExc, DispatcherException,
)
from lucky_bot.bot_config import BOT

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)


def send_message(uid: int, text: str, file=None):
    """
    Send a message to Telegram and handle exceptions.

    Raises:
        DispatcherException
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

        except ApiTelegramException as aexc:
            if TG_WRONG_TOKEN.search(aexc.description):
                msg = 'dispatcher: wrong telegram token'
                logger.exception(msg)
                event.error(msg)
                console(msg)
                raise DispatcherWrongToken(msg)

            elif TG_UID_NOT_FOUND.search(aexc.description):
                msg = 'dispatcher: uid not found'
                event.warning(msg)
                console(msg)
                raise DispatcherNoAccess(msg)

            elif TG_BOT_BLOCKED.search(aexc.description):
                msg = 'dispatcher: bot blocked'
                event.warning(msg)
                console(msg)
                raise DispatcherNoAccess(msg)

            elif TG_BOT_TIMEOUT.search(aexc.description):
                if attempt < 3:
                    time.sleep(10)
                    continue
                else:
                    msg = 'dispatcher: telegram timeout'
                    event.warning(msg)
                    console(msg)
                    raise DispatcherTimeout(msg)

            else:
                if attempt < 3:
                    time.sleep(1)
                    continue
                else:
                    msg = 'dispatcher: undefined ApiTelegramException'
                    event.warning(msg)
                    console(msg)
                    raise DispatcherUndefinedExc(msg)

        except Exception as exception:
            msg = 'dispatcher: normal exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            raise DispatcherException(exception)

        else:
            break
