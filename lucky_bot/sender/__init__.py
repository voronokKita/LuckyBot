""" Sender.
A module that handles output messages to Telegram.
Consists of the sender thread, the output message queue and the output dispatcher.
The module can send messages to the input message queue.
"""
from .output_mq import OutputQueue
from .sender import SenderThread
