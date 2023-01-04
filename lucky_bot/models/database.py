from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import DB_FILE

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

DB_ENGINE = create_engine(f'sqlite:///{DB_FILE}', future=True)

DB_SESSION = sessionmaker(bind=DB_ENGINE)

MainBase = declarative_base()


class User(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False)

    def __str__(self):
        return f'<user #{self.tg_id!r}>'
