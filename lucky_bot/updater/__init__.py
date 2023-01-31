""" Updater.
A module that handles distribution of messages to the users on a schedule.
Consists of the updater thread and the update dispatcher.
The module is coupled with the main database and the output message queue.
"""
from . import update_dispatcher
from .updater import UpdaterThread
