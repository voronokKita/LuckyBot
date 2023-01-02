from sqlalchemy import (
    create_engine,
    Column, Integer, Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from lucky_bot.helpers.constants import DB_URI

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

db_engine = create_engine(f'sqlite:///{DB_URI}', future=True)
main_db_session = sessionmaker(bind=db_engine)

MainBase = declarative_base()


class User(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, nullable=False)

    def __str__(self):
        return f'<user #{self.tg_id!r}>'
