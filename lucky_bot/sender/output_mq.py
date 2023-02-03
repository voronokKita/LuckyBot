"""
Output Message Queue.
It saves messages from the program, for future sending to Telegram.
Raises: OMQException
"""
from time import time as current_time

from sqlalchemy import create_engine, Column, Integer, BLOB, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import TESTING, OUTPUT_MQ_FILE, OMQException
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
    destination = Column('address', BLOB, nullable=False)
    text = Column('message_text', BLOB, nullable=False)
    stream = Column('file', BLOB, nullable=True, default=None)
    markup = Column('markup_text?', Boolean, nullable=False, default=False)
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
    def add_message(uid: str | int, message: str, time=None,
                    file=None, markup=False, encrypted=False) -> True:
        """ Cypher any data. """
        test_func2()
        if not time:
            time = int(current_time())

        if not encrypted:
            uid = encrypt(str(uid).encode())
            message = encrypt(message.encode())

        with OMQ_SESSION.begin() as session:
            msg_obj = OutgoingMessage(destination=uid, text=message, time=time, markup=markup)
            session.add(msg_obj)
        return True

    @staticmethod
    @catch_exception
    def get_first_message() -> tuple | None:
        """
        Decipher and return original data, if any.

        Returns:
            tuple: (message_id, uid, text, markup)

            None: if the queue is empty
        """
        test_func()
        with OMQ_SESSION() as session:
            msg_obj = session.query(OutgoingMessage)\
                .order_by(OutgoingMessage.time)\
                .first()
            if not msg_obj:
                return None

            uid = decrypt(msg_obj.destination)
            text = decrypt(msg_obj.text)
            return msg_obj.id, uid, text, msg_obj.markup

    @staticmethod
    @catch_exception
    def delete_message(msg_id: int) -> bool:
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
