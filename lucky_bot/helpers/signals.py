""" All the threading.Event settings. """
from threading import Event


class SignalThreadStarted(Event):
    """ A thread has successfully started. """

class SignalThreadStopped(Event):
    """ A thread has successfully stopped. """

class SignalThreadsAreStarted(Event):
    """ All the threads have started. """

class SignalExit(Event):
    """ Some event demands to stop the program. """

class SignalAllDone(Event):
    """ main.py signaling just before the exit for the testing purposes. """

class SignalIncomingMessage(Event):
    """ A new message in the receiver message queue (rmq). """

class SignalMessageToSend(Event):
    """ A new message to telegram in the sender message queue (smq). """

class SignalUpdater(Event):
    """ A new updater cycle. """


# Threading signals
SENDER_IS_RUNNING = SignalThreadStarted()
UPDATER_IS_RUNNING = SignalThreadStarted()
CONTROLLER_IS_RUNNING = SignalThreadStarted()
RECEIVER_IS_RUNNING = SignalThreadStarted()

SENDER_IS_STOPPED = SignalThreadStopped()
UPDATER_IS_STOPPED = SignalThreadStopped()
CONTROLLER_IS_STOPPED = SignalThreadStopped()
RECEIVER_IS_STOPPED = SignalThreadStopped()

ALL_THREADS_ARE_GO = SignalThreadsAreStarted()


# Other
INCOMING_MESSAGE = SignalIncomingMessage()
NEW_MESSAGE_TO_SEND = SignalMessageToSend()
UPDATER_CYCLE = SignalUpdater()

EXIT_SIGNAL = SignalExit()

ALL_DONE_SIGNAL = SignalAllDone()


def exit_signal(signal_=None, frame=None):
    """ System SIGINT and SIGTSTP. """
    print()
    EXIT_SIGNAL.set()
