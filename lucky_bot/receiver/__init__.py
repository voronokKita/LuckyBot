""" Receiver.
A module that handles input messages from Telegram.
"""
from .input_mq import InputQueue
from .flask_config import FLASK_APP
from .receiver import ReceiverThread
