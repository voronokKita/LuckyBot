from sqlalchemy import create_engine, Column, Integer, Text, BLOB
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import TESTING, OUTPUT_MQ_FILE

import logging
logger = logging.getLogger(__name__)

OMQ_ENGINE = create_engine(f'sqlite:///{OUTPUT_MQ_FILE}', future=True)

OMQ_SESSION = sessionmaker(bind=OMQ_ENGINE)

OMQBase = declarative_base()


class OutgoingMessage(OMQBase):
    __tablename__ = 'messages_to_telegram'

    id = Column(Integer, primary_key=True)
    text = Column('message_text', Text, nullable=False)
    stream = Column('message_file', BLOB, nullable=True)
    time = Column('message_date', Integer, nullable=False)

    def __str__(self):
        return f'<outgoing message id-{self.id!r}>'


class OutputQueue:
    @staticmethod
    def set_up():
        OMQBase.metadata.create_all(OMQ_ENGINE)

    @staticmethod
    def tear_down():
        if TESTING and OUTPUT_MQ_FILE.exists():
            OMQBase.metadata.drop_all(OMQ_ENGINE)

    @staticmethod
    def add_message(message, date, file=None):
        msg_obj = OutgoingMessage(text=message, time=date)
        with OMQ_SESSION.begin() as session:
            session.add(msg_obj)

    @staticmethod
    def get_first_message() -> Query | None:
        ''' FIFO '''
        with OMQ_SESSION() as session:
            msg_obj = session.query(OutgoingMessage)\
                .order_by(OutgoingMessage.time).first()
            return msg_obj

    @staticmethod
    def delete_message(msg_obj):
        with OMQ_SESSION.begin() as session:
            session.delete(msg_obj)


if not TESTING and not OUTPUT_MQ_FILE.exists():
    OutputQueue.set_up()
