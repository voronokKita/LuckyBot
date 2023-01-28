""" Main database and its models. """
from time import time
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, Column, ForeignKey,
    Integer, Text, DateTime, BLOB, Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Query
from sqlalchemy.exc import IntegrityError

from lucky_bot.helpers.constants import DB_FILE, TESTING, LAST_NOTES_LIST, DatabaseException

import logging
from logs import console, event
logger = logging.getLogger(__name__)

def test_func(): pass

def test_func2(): pass

def catch_exception(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            msg = f'main db: {func.__name__}() exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            raise DatabaseException(exc)
        else:
            return result

    return wrapper

DB_ENGINE = create_engine(f'sqlite:///{DB_FILE}', future=True)

DB_SESSION = sessionmaker(bind=DB_ENGINE)

MainBase = declarative_base()


class User(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column('telegram_id', Integer, nullable=False, unique=True, index=True)
    last_note = Column('last_note_num', Integer, nullable=False, default=0)
    notes_total = Column('notes_total', Integer, nullable=False, default=0)

    got_first_update = Column('first_note_sent?', Boolean, nullable=False, default=False)
    got_second_update = Column('second_note_sent?', Boolean, nullable=False, default=False)

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
        order_by='LastNoteSent.time',
    )


class Note(MainBase):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    number = Column('user_note_num', Integer, nullable=False)
    text = Column('note_text', Text, nullable=False)
    stream = Column('file', BLOB, nullable=True)
    date = Column('date_added', DateTime, nullable=False)

    user = relationship(User, back_populates='notes')


class LastNoteSent(MainBase):
    __tablename__ = 'last_updates'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    note_number = Column('user_note_num', Integer, nullable=False)
    time = Column('time_added', Integer, nullable=False)

    user = relationship(User, back_populates='last_notes')


class MainDB:
    """
    Wrapper for the queries to the main database.
    Note:
        There is uncertainty in the system.
        Requests can arrive even if the user has already been deleted,
        a function can query for user notes that no longer exist.
        For this reason, functions tend not to throw exceptions.
    """

    @staticmethod
    @catch_exception
    def set_up():
        MainBase.metadata.create_all(DB_ENGINE)

    @staticmethod
    @catch_exception
    def tear_down():
        if TESTING and DB_FILE.exists():
            MainBase.metadata.drop_all(DB_ENGINE)

    @staticmethod
    @catch_exception
    def add_user(uid) -> bool:
        """ Will return False if the user already exists. """
        test_func()
        try:
            with DB_SESSION.begin() as session:
                user = User(tg_id=uid)
                session.add(user)
        except IntegrityError:
            return False
        else:
            return True

    @staticmethod
    @catch_exception
    def add_note(uid, text, file=None) -> bool:
        """ Will return False if the user don't exist. """
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
        return True

    @staticmethod
    @catch_exception
    def delete_user(uid) -> bool:
        """ Will return False if the user don't exist. """
        with DB_SESSION.begin() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if not user:
                return False
            else:
                session.delete(user)
        return True

    @staticmethod
    @catch_exception
    def delete_user_note(uid, note_num) -> bool:
        """ Will return False if the note is not found. """
        with DB_SESSION.begin() as session:
            note = session.query(Note).join(User) \
                .filter(User.tg_id == uid, Note.number == note_num) \
                .first()
            if not note:
                return False
            else:
                note.user.notes_total -= 1
                session.delete(note)
        return True

    @staticmethod
    @catch_exception
    def update_user_note(uid, note_num, new_text) -> bool:
        """ Will return False if the note is not found. """
        with DB_SESSION.begin() as session:
            note = session.query(Note).join(User) \
                .filter(User.tg_id == uid, Note.number == note_num) \
                .first()
            if not note:
                return False
            else:
                note.text = new_text
                note.date = datetime.now(timezone.utc).replace(microsecond=0)
        return True

    @staticmethod
    @catch_exception
    def update_user_last_notes_list(uid, note_num) -> bool:
        """
        Will return False if the user don't exist.
        Will skip and return True if user's total notes is <= than LAST_NOTES_LIST.
        If user's last notes is == to LAST_NOTES_LIST:
        will pop the 1st element from user's last_notes list, append the new one,
        """
        with DB_SESSION.begin() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if not user:
                return False
            elif user.notes_total <= LAST_NOTES_LIST:
                return True

            if user.last_notes and len(user.last_notes) == LAST_NOTES_LIST:
                session.delete(user.last_notes[0])

            last_note = LastNoteSent(
                note_number=note_num,
                time=int(time()),
            )
            user.last_notes.append(last_note)
        return True

    @staticmethod
    @catch_exception
    def clear_all_users_flags() -> bool:
        """ Will return False if the user don't exist. """
        with DB_SESSION.begin() as session:
            users = session.query(User).filter().all()
            if not users:
                return False
            for user in users:
                if user.got_first_update:
                    user.got_first_update = False
                if user.got_second_update:
                    user.got_second_update = False
        return True

    @staticmethod
    @catch_exception
    def set_user_flag(uid, flag: str) -> bool:
        """ Will return False if the user don't exist. """
        with DB_SESSION.begin() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if not user:
                return False
            if flag == 'first update':
                user.got_first_update = True
            elif flag == 'second update':
                user.got_second_update = True
        return True

    @staticmethod
    @catch_exception
    def get_user(uid) -> Query | None:
        with DB_SESSION() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            return user

    @staticmethod
    @catch_exception
    def get_user_note(uid, note_num) -> Query | None:
        with DB_SESSION() as session:
            note = session.query(Note).join(User) \
                .filter(User.tg_id == uid, Note.number == note_num) \
                .first()
            return note

    @staticmethod
    @catch_exception
    def get_user_notes(uid) -> list:
        """
        Will return an empty list if the user don't exist.
        Will return an empty list if there is no user's notes.
        Notes are ordered by the Note.number, ascending.
        """
        with DB_SESSION() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            return user.notes if user else []

    @staticmethod
    @catch_exception
    def get_users_with_notes() -> list:
        """ Will return an empty list if no users with notes found. """
        with DB_SESSION() as session:
            users = session.query(User).filter(User.notes_total != 0).all()
            return users

    @staticmethod
    @catch_exception
    def get_notifications_for_the_updater(uid) -> list:
        """
        Will return an empty list if the user don't exist.

        if total user notes <= LAST_NOTES_LIST, will return all user notes;
        else, will return notes, except for the notes from user's last_notes list.
        """
        test_func2()
        with DB_SESSION() as session:
            user = session.query(User).filter(User.tg_id == uid).first()
            if not user:
                return []

            if user.notes_total > LAST_NOTES_LIST and user.last_notes:
                l = [n.note_number for n in user.last_notes]
                notes = session.query(Note).join(User) \
                    .filter(User.tg_id == uid, Note.number.not_in(l)).all()
            else:
                notes = user.notes

            return notes


if not TESTING and not DB_FILE.exists():
    MainBase.set_up()
