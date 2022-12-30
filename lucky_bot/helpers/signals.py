from threading import Event


class SignalThreadStarted(Event):
    ''' Thread started successfully. '''

class SignalThreadStopped(Event):
    ''' Thread stopped successfully. '''

class SignalThreadsAreStarted(Event):
    ''' All the threads - webhook, input controller, updater and sender, - are started. '''

class SignalExit(Event):
    ''' Some event is demanding to stop the program. '''

class SignalAllDone(Event):
    ''' main.py signaling just before the exit. '''

class SignalTgMessage(Event):
    ''' A new telegram message in the receiver queue. '''


# Threading signals
SENDER_IS_RUNNING = SignalThreadStarted()
UPDATER_IS_RUNNING = SignalThreadStarted()
INPUT_CONTROLLER_IS_RUNNING = SignalThreadStarted()
WEBHOOK_IS_RUNNING = SignalThreadStarted()

SENDER_IS_STOPPED = SignalThreadStopped()
UPDATER_IS_STOPPED = SignalThreadStopped()
INPUT_CONTROLLER_IS_STOPPED = SignalThreadStopped()
WEBHOOK_IS_STOPPED = SignalThreadStopped()

ALL_THREADS_ARE_GO = SignalThreadsAreStarted()

EXIT_SIGNAL = SignalExit()

ALL_DONE_SIGNAL = SignalAllDone()

# Other
NEW_TELEGRAM_MESSAGE = SignalTgMessage()


def exit_signal(signal_=None, frame=None):
    ''' SIGINT and SIGTSTP. '''
    print()
    EXIT_SIGNAL.set()
