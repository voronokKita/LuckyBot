from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import INPUT_MQ

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

input_messages_engine = create_engine(f'sqlite:///{INPUT_MQ}', future=True)
input_session = sessionmaker(bind=input_messages_engine)

InputBase = declarative_base()


class InputMessage(InputBase):
    __tablename__ = 'input_messages'

    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)

    def __str__(self):
        return f'<tg message id-{self.id!r}>'
