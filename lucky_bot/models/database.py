""" Main database and its model. """
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, Column, ForeignKey,
    Integer, Text, DateTime, BLOB,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Query
from sqlalchemy.exc import IntegrityError

from lucky_bot.helpers.constants import DB_FILE, TESTING

import logging
from logs.config import console, event
logger = logging.getLogger(__name__)

DB_ENGINE = create_engine(f'sqlite:///{DB_FILE}', future=True)

DB_SESSION = sessionmaker(bind=DB_ENGINE)

MainBase = declarative_base()


class User(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column('telegram_id', Integer, nullable=False, unique=True, index=True)
    last_note = Column('last_note_num', Integer, nullable=False, default=0)

    notes = relationship('Note', back_populates='user', cascade='all, delete-orphan')

    def __str__(self):
        return f'<user #{self.tg_id!r}>'


class Note(MainBase):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    number = Column('user_note_num', Integer, nullable=False)
    text = Column('note_text', Text, nullable=False)
    stream = Column('file', BLOB, nullable=True)
    date = Column('date_added', DateTime, nullable=False)

    user = relationship(User, back_populates='notes')

    def __str__(self):
        return f'<note #{self.id!r}>'


class MainDB:
    """ Wrapper for the queries to the main database. """

    @staticmethod
    def set_up():
        MainBase.metadata.create_all(DB_ENGINE)

    @staticmethod
    def tear_down():
        if TESTING and DB_FILE.exists():
            MainBase.metadata.drop_all(DB_ENGINE)

    @staticmethod
    def add_user(uid) -> bool:
        try:
            with DB_SESSION.begin() as session:
                user = User(tg_id=uid)
                session.add(user)
        except IntegrityError:
            return False
        else:
            return True

    @staticmethod
    def get_user(uid) -> Query | None:
        with DB_SESSION() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            return user

    @staticmethod
    def add_note(uid, text, file=None) -> True:
        with DB_SESSION.begin() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if not user:
                user = User(tg_id=uid, last_note=0)
                session.add(user)

            note = Note(
                number=user.last_note + 1,
                text=text,
                date=datetime.now(timezone.utc),  # TODO
            )
            user.notes.append(note)
            user.last_note += 1
        return True

    @staticmethod
    def get_user_notes(uid) -> Query | None:
        with DB_SESSION() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if user:
                return user.notes
            else:
                return None
