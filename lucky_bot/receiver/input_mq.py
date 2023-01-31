"""
Input Message Queue.
Saves a message data from Telegram, or internal and admin commands, for future processing.
Raises: IMQException
"""
from time import time

from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import TESTING, INPUT_MQ_FILE, IMQException

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
            msg = f'input mq: {func.__name__}() exception'
            logger.exception(msg)
            Log.critical(msg)
            raise IMQException(exc)
        else:
            return result

    return wrapper

IMQBase = declarative_base()


class IncomingMessage(IMQBase):
    __tablename__ = 'incoming_messages'

    id = Column(Integer, primary_key=True)
    data = Column('message_body', Text, nullable=False)
    time = Column('message_date', Integer, nullable=False)

    def __str__(self):
        return f'<input message id-{self.id!r}>'


IMQ_ENGINE = create_engine(f'sqlite:///{INPUT_MQ_FILE}', future=True)
IMQ_SESSION = sessionmaker(bind=IMQ_ENGINE)


class InputQueue:
    """ Wrapper for the queries to the input message queue. """

    @staticmethod
    @catch_exception
    def set_up():
        IMQBase.metadata.create_all(IMQ_ENGINE)

    @staticmethod
    @catch_exception
    def tear_down():
        if TESTING and INPUT_MQ_FILE.exists():
            IMQBase.metadata.drop_all(IMQ_ENGINE)

    @staticmethod
    @catch_exception
    def add_message(data, date=None):
        test_func()
        if not date:
            date = int(time())
        with IMQ_SESSION.begin() as session:
            msg_obj = IncomingMessage(data=data, time=date)
            session.add(msg_obj)

    @staticmethod
    @catch_exception
    def get_first_message() -> Query | None:
        """ FIFO """
        test_func2()
        with IMQ_SESSION() as session:
            msg_obj = session.query(IncomingMessage)\
                .order_by(IncomingMessage.time)\
                .first()
            return msg_obj

    @staticmethod
    @catch_exception
    def delete_message(msg_obj):
        with IMQ_SESSION.begin() as session:
            session.delete(msg_obj)


if not TESTING and not INPUT_MQ_FILE.exists():
    InputQueue.set_up()
