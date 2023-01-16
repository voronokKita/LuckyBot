""" Sender.

A module that handles output messages to Telegram.
"""
from .output_mq import OutputQueue
from . import dispatcher
from .sender import SenderThread
