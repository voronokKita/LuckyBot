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
from logs import console, event
logger = logging.getLogger(__name__)

DB_ENGINE = create_engine(f'sqlite:///{DB_FILE}', future=True)

DB_SESSION = sessionmaker(bind=DB_ENGINE)

MainBase = declarative_base()


class User(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column('telegram_id', Integer, nullable=False, unique=True, index=True)
    last_note = Column('last_note_num', Integer, nullable=False, default=0)
    notes_total = Column('notes_total', Integer, nullable=False, default=0)

    notes = relationship(
        'Note',
        back_populates='user',
        cascade='all, delete-orphan',
        order_by='Note.number',
    )
    last_notes = relationship(
        'LastNoteSent',
        back_populates='user',
        cascade='all, delete-orphan',
    )

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


class LastNoteSent(MainBase):
    __tablename__ = 'last_updates'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    csv_list = Column('csv_list', Text, nullable=False)

    user = relationship(User, back_populates='last_notes')

    def __str__(self):
        return f'<csv list #{self.id!r}>'


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
        """ Will return False if the user already exists. """
        try:
            with DB_SESSION.begin() as session:
                user = User(tg_id=uid)
                session.add(user)
        except IntegrityError:
            return False
        except Exception:
            msg = 'main db: add user exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
        else:
            return True

    @staticmethod
    def get_user(uid) -> Query | None:
        try:
            with DB_SESSION() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                return user
        except Exception:
            msg = 'main db: get user exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return None

    @staticmethod
    def add_note(uid, text, file=None) -> bool:
        try:
            with DB_SESSION.begin() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return False

                note = Note(
                    number=user.last_note + 1,
                    text=text,
                    date=datetime.now(timezone.utc).replace(microsecond=0),
                )
                user.notes.append(note)
                user.last_note += 1
                user.notes_total += 1
        except Exception:
            msg = 'main db: add note exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False
        else:
            return True

    @staticmethod
    def get_user_notes(uid) -> list | None:
        """ Notes are ordered by the Note.number, ascending. """
        try:
            with DB_SESSION() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return None
                else:
                    return user.notes
        except Exception:
            msg = 'main db: get notes exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return None

    @staticmethod
    def get_notifications_for_the_updater(uid) -> Query | None:
        """
        if total user notes <= 10, will return all user notes;
        else, will return notes, except for the notes from the user last_notes list.
        """
        def filter_last_notes(note_number, last_notes_list):
            for n in last_notes_list:
                if n == note_number:
                    return False
            return True

        try:
            with DB_SESSION() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return None

                if user.notes_total > 10:
                    last_notes = user.last_notes.csv_list.split(',')
                else:
                    last_notes = []

                notes = session.query(Note).join(User) \
                    .filter(User.tg_id == uid, filter_last_notes(Note.number, last_notes))

                if not notes:
                    return None
                else:
                    return notes
        except Exception:
            msg = 'main db: get notes for the updater exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return None

    def update_user_last_notes_list(self):
        ''' TODO '''
        pass

    @staticmethod
    def get_user_note(uid, note_num) -> Query | None:
        """ Will return None if not found. """
        try:
            with DB_SESSION() as session:
                note = session.query(Note).join(User) \
                    .filter(User.tg_id == uid, Note.number == note_num) \
                    .first()
                if not note:
                    return None
                else:
                    return note
        except Exception:
            msg = 'main db: get a note exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return None

    @staticmethod
    def delete_user_note(uid, note_num) -> bool:
        """ Will return False if not found. """
        try:
            with DB_SESSION.begin() as session:
                note = session.query(Note).join(User)\
                    .filter(User.tg_id == uid, Note.number == note_num)\
                    .first()
                if not note:
                    return False
                else:
                    note.user.notes_total -= 1
                    session.delete(note)
        except Exception:
            msg = 'main db: delete not list exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False
        else:
            return True

    @staticmethod
    def delete_user(uid) -> bool:
        """ Will return False if not found. """
        try:
            with DB_SESSION.begin() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return False
                else:
                    session.delete(user)
        except Exception:
            msg = 'main db: delete user exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False
        else:
            return True

    @staticmethod
    def update_user_note(uid, note_num, new_text) -> bool:
        """ Will return False if not found. """
        try:
            with DB_SESSION.begin() as session:
                note = session.query(Note).join(User) \
                    .filter(User.tg_id == uid, Note.number == note_num) \
                    .first()
                if not note:
                    return False
                else:
                    note.text = new_text
                    note.date = datetime.now(timezone.utc).replace(microsecond=0)
        except Exception:
            msg = 'main db: update note exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False
        else:
            return True


if not TESTING and not DB_FILE.exists():
    MainBase.set_up()
