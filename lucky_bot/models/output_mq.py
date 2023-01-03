from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import OUTPUT_MQ_FILE

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

output_messages_engine = create_engine(f'sqlite:///{OUTPUT_MQ_FILE}', future=True)
output_session = sessionmaker(bind=output_messages_engine)

OutputBase = declarative_base()


class OutputMessage(OutputBase):
    __tablename__ = 'output_messages'

    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)

    def __str__(self):
        return f'<outgoing message id-{self.id!r}>'
