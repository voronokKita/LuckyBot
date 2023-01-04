from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import OUTPUT_MQ_FILE

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

OMQ_ENGINE = create_engine(f'sqlite:///{OUTPUT_MQ_FILE}', future=True)

OMQ_SESSION = sessionmaker(bind=OMQ_ENGINE)

OMQBase = declarative_base()


class OutputMessage(OMQBase):
    __tablename__ = 'messages_to_telegram'

    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)
    time = Column('message_date', Integer, nullable=False)

    def __str__(self):
        return f'<outgoing message id-{self.id!r}>'
