from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Query

from lucky_bot.helpers.constants import TESTING, INPUT_MQ_FILE

import logging
logger = logging.getLogger(__name__)

IMQ_ENGINE = create_engine(f'sqlite:///{INPUT_MQ_FILE}', future=True)

IMQ_SESSION = sessionmaker(bind=IMQ_ENGINE)

IMQBase = declarative_base()


class TGMessage(IMQBase):
    __tablename__ = 'messages_from_telegram'

    id = Column(Integer, primary_key=True)
    data = Column('message_data', Text, nullable=False)
    time = Column('message_date', Integer, nullable=False)

    def __str__(self):
        return f'<tg message id-{self.id!r}>'


class InputQueue:
    @staticmethod
    def set_up():
        if not INPUT_MQ_FILE.exists():
            IMQBase.metadata.create_all(IMQ_ENGINE)

    @staticmethod
    def tear_down():
        if TESTING and INPUT_MQ_FILE.exists():
            INPUT_MQ_FILE.unlink()
        else:
            IMQBase.metadata.drop_all(IMQ_ENGINE)

    @staticmethod
    def add_message(data, date):
        msg_obj = TGMessage(data=data, time=date)
        with IMQ_SESSION.begin() as session:
            session.add(msg_obj)

    @staticmethod
    def get_first_message() -> Query | None:
        ''' FIFO '''
        with IMQ_SESSION() as session:
            msg_obj = session.query(TGMessage).order_by(TGMessage.time).first()
            return msg_obj

    @staticmethod
    def delete_message(msg_obj):
        with IMQ_SESSION.begin() as session:
            session.delete(msg_obj)


if not TESTING and not INPUT_MQ_FILE.exists():
    InputQueue.set_up()
