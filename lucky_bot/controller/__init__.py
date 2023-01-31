""" Controller.
A module that handles incoming Telegram messages, the internal and admin commands.
Consists of the controller thread, the telebot handlers, the data parser and the command responder.
The module is coupled with the main database and the output message queue.
"""
from .responder import Respond
from .controller import ControllerThread
from . import bot_handlers  # important
