from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import INPUT_MQ

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

input_messages_engine = create_engine(f'sqlite:///{INPUT_MQ}', future=True)
INPUT_SESSION = sessionmaker(bind=input_messages_engine)

InputBase = declarative_base()


class TGMessage(InputBase):
    __tablename__ = 'messages_from_telegram'

    id = Column(Integer, primary_key=True)
    data = Column('message_data', Text, nullable=False)
    time = Column('message_date', Integer, nullable=False)

    def __str__(self):
        return f'<tg message id-{self.id!r}>'


class InputQueue:
    @staticmethod
    def add_message(data, date):
        msg_obj = TGMessage(data=data, time=date)
        with INPUT_SESSION.begin() as session:
            session.add(msg_obj)

    @staticmethod
    def get_first_message() -> Query | None:
        ''' FIFO '''
        with INPUT_SESSION() as session:
            msg_obj = session.query(TGMessage).order_by('time').first()
            return msg_obj

    @staticmethod
    def delete_message(msg_obj):
        with INPUT_SESSION.begin() as session:
            session.delete(msg_obj)


if not INPUT_MQ.exists():
    InputBase.metadata.create_all(input_messages_engine)
