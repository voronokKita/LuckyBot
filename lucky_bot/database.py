""" Main database and its model. """
from time import time
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, Column, ForeignKey,
    Integer, Text, DateTime, BLOB, Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Query
from sqlalchemy.exc import IntegrityError

from lucky_bot.helpers.constants import DB_FILE, TESTING, LAST_NOTES_LIST

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
            return True

        except IntegrityError:
            return False
        except Exception:
            msg = 'main db: add user exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)

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
    def get_users_with_notes() -> list | None:
        try:
            with DB_SESSION() as session:
                users = session.query(User).filter(User.notes_total != 0).all()
                return users
        except Exception:
            msg = 'main db: get users exception'
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
            return True

        except Exception:
            msg = 'main db: add note exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False

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
            return True

        except Exception:
            msg = 'main db: delete not list exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False

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
            return True

        except Exception:
            msg = 'main db: delete user exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False

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
            return True

        except Exception:
            msg = 'main db: update note exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return False

    @staticmethod
    def get_notifications_for_the_updater(uid) -> list | None:
        """
        if total user notes <= 10, will return all user notes;
        else, will return notes, except for the notes from the user last_notes list.
        """
        try:
            with DB_SESSION() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return None

                if user.notes_total > LAST_NOTES_LIST and user.last_notes:
                    l = [n.note_number for n in user.last_notes]
                    notes = session.query(Note).join(User) \
                        .filter(User.tg_id == uid, Note.number.not_in(l)).all()
                else:
                    notes = user.notes

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

    @staticmethod
    def update_user_last_notes_list(uid, note_num) -> bool:
        """ Pop the 1st element from the user last_notes list, append the new one. """
        try:
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

        except Exception:
            msg = "main db: update user's last_notes list exception"
            logger.exception(msg)
            event.error(msg)
            console(msg)
            return None

    @staticmethod
    def clear_all_users_flags():
        try:
            with DB_SESSION.begin() as session:
                users = session.query(User).filter().all()
                if not users:
                    return
                for user in users:
                    if user.got_first_update:
                        user.got_first_update = False
                    if user.got_second_update:
                        user.got_second_update = False

        except Exception:
            msg = 'main db: clear all flags exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)

    @staticmethod
    def set_user_flag(uid, flag:str):
        try:
            with DB_SESSION.begin() as session:
                user = session.query(User).filter(User.tg_id == uid).first()
                if not user:
                    return
                if flag == 'first update':
                    user.got_first_update = True
                elif flag == 'second update':
                    user.got_second_update = True

        except Exception:
            msg = 'main db: set a flag exception'
            logger.exception(msg)
            event.error(msg)
            console(msg)


if not TESTING and not DB_FILE.exists():
    MainBase.set_up()
