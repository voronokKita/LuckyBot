"""
Output Message Queue.
It saves messages from the program, for future sending to Telegram.
Raises: OMQException
"""
from time import time as current_time

from sqlalchemy import create_engine, Column, Integer, BLOB
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import TESTING, OUTPUT_MQ_FILE, IMQ_SECRET, OMQException
from lucky_bot.helpers.misc import encrypt, decrypt

import logging
logger = logging.getLogger(__name__)
from logs import Log

def test_func(): pass

def test_func2(): pass

def catch_exception(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            msg = f'output mq: {func.__name__}() exception'
            logger.exception(msg)
            Log.critical(msg)
            raise OMQException(exc)
        else:
            return result

    return wrapper

OMQBase = declarative_base()


class OutgoingMessage(OMQBase):
    __tablename__ = 'messages_to_telegram'

    id = Column(Integer, primary_key=True)
    destination = Column('address', Integer, nullable=False)
    text = Column('message_text', BLOB, nullable=False)
    stream = Column('file', BLOB, nullable=True, default=None)
    time = Column('date', Integer, nullable=False)


OMQ_ENGINE = create_engine(f'sqlite:///{OUTPUT_MQ_FILE}', future=True)
OMQ_SESSION = sessionmaker(bind=OMQ_ENGINE)


class OutputQueue:
    """ Wrapper for the queries to the output message queue. FIFO. """
    @staticmethod
    @catch_exception
    def set_up():
        OMQBase.metadata.create_all(OMQ_ENGINE)

    @staticmethod
    @catch_exception
    def tear_down():
        if TESTING and OUTPUT_MQ_FILE.exists():
            OMQBase.metadata.drop_all(OMQ_ENGINE)

    @staticmethod
    @catch_exception
    def add_message(uid, message, time=None, file=None, encrypted=False) -> True:
        """ Cypher any data. """
        test_func2()
        if not time:
            time = int(current_time())

        if not encrypted:
            message = encrypt(message.encode(), IMQ_SECRET)

        with OMQ_SESSION.begin() as session:
            msg_obj = OutgoingMessage(destination=uid, text=message, time=time)
            session.add(msg_obj)
        return True

    @staticmethod
    @catch_exception
    def get_first_message() -> tuple | None:
        """
        Decipher and return original data, if any.

        Returns:
            tuple: (message_id, uid, text)

            None: if the queue is empty
        """
        test_func()
        with OMQ_SESSION() as session:
            msg_obj = session.query(OutgoingMessage)\
                .order_by(OutgoingMessage.time)\
                .first()
            if not msg_obj:
                return None

            text = decrypt(msg_obj.text, IMQ_SECRET)
            return msg_obj.id, msg_obj.destination, text

    @staticmethod
    @catch_exception
    def delete_message(msg_id:int) -> bool:
        with OMQ_SESSION.begin() as session:
            msg_obj = session.query(OutgoingMessage)\
                .filter(OutgoingMessage.id == msg_id)\
                .first()
            if not msg_obj:
                return False
            session.delete(msg_obj)
        return True


if not TESTING and not OUTPUT_MQ_FILE.exists():
    OutputQueue.set_up()
