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


SENDER_IS_RUNNING: SignalThreadStarted = Event()
UPDATER_IS_RUNNING: SignalThreadStarted = Event()
INPUT_CONTROLLER_IS_RUNNING: SignalThreadStarted = Event()
WEBHOOK_IS_RUNNING: SignalThreadStarted = Event()

SENDER_IS_STOPPED: SignalThreadStopped = Event()
UPDATER_IS_STOPPED: SignalThreadStopped = Event()
INPUT_CONTROLLER_IS_STOPPED: SignalThreadStopped = Event()
WEBHOOK_IS_STOPPED: SignalThreadStopped = Event()

ALL_THREADS_ARE_GO: SignalThreadsAreStarted = Event()

EXIT_SIGNAL: SignalExit = Event()

ALL_DONE_SIGNAL: SignalAllDone = Event()
