"""
Output Message Queue.
It saves messages from the program, for future sending to Telegram.
Raises: OMQException
"""
from time import time

from sqlalchemy import create_engine, Column, Integer, Text, BLOB
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import TESTING, OUTPUT_MQ_FILE, OMQException

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
    text = Column('message_text', Text, nullable=False)
    stream = Column('file', BLOB, nullable=True)
    time = Column('date', Integer, nullable=False)


OMQ_ENGINE = create_engine(f'sqlite:///{OUTPUT_MQ_FILE}', future=True)
OMQ_SESSION = sessionmaker(bind=OMQ_ENGINE)


class OutputQueue:
    """ Wrapper for the queries to the output message queue. """
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
    def add_message(uid, message, date=None, file=None):
        test_func2()
        if not date:
            date = int(time())
        with OMQ_SESSION.begin() as session:
            msg_obj = OutgoingMessage(destination=uid, text=message, time=date)
            session.add(msg_obj)

    @staticmethod
    @catch_exception
    def get_first_message() -> Query | None:
        """ FIFO """
        test_func()
        with OMQ_SESSION() as session:
            msg_obj = session.query(OutgoingMessage)\
                .order_by(OutgoingMessage.time)\
                .first()
            return msg_obj

    @staticmethod
    @catch_exception
    def delete_message(msg_obj):
        with OMQ_SESSION.begin() as session:
            session.delete(msg_obj)


if not TESTING and not OUTPUT_MQ_FILE.exists():
    OutputQueue.set_up()
