import sys
import threading

from lucky_bot.helpers.constants import MainError, TREAD_RUNNING_TIMEOUT
from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
)
from lucky_bot.sender import SenderThread
from lucky_bot.updater import UpdaterThread
from lucky_bot.input_controller import InputControllerThread
from lucky_bot.webhook import WebhookThread


class MainAsThread(threading.Thread):
    ''' The main reason for this class is testing. '''
    exception = None

    def __str__(self):
        return 'main thread (well, not exactly)'

    def __int__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            main()
        except Exception as e:
            self.exception = e

    def merge(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        threading.Thread.join(self, 5)
        if self.exception:
            raise self.exception


def main():
    # instantiate threads;
    sender = SenderThread()
    updater = UpdaterThread()
    input_controller = InputControllerThread()
    webhook = WebhookThread()

    threads = [
        {'thread': sender, 'running': SENDER_IS_RUNNING},
        {'thread': updater, 'running': UPDATER_IS_RUNNING},
        {'thread': input_controller, 'running': INPUT_CONTROLLER_IS_RUNNING},
        {'thread': webhook, 'running': WEBHOOK_IS_RUNNING},
    ]

    # run all the threads;
    active_threads = []
    for unit in threads:
        unit['thread'].start()
        active_threads.append(unit)
        if unit['running'].wait(TREAD_RUNNING_TIMEOUT):
            if EXIT_SIGNAL.is_set():
                thread_loading_error(active_threads)
        else:
            thread_loading_timeout(unit['thread'], active_threads)

    del threads
    ALL_THREADS_ARE_GO.set()

    # just sleep and wait for the exit signal;
    if EXIT_SIGNAL.wait():
        pass

    # done.
    finish_the_work(active_threads)


def thread_loading_timeout(thread, active_threads):
    EXIT_SIGNAL.set()
    msg = f'Failed to start the threads: {thread} timeout.'
    finish_the_work(active_threads, MainError(msg))


def thread_loading_error(active_threads):
    msg = 'Failed to start the threads: exception occurred.'
    finish_the_work(active_threads, MainError(msg))


def finish_the_work(active_threads, main_error=None):
    exception_in_threads = stop_active_threads(active_threads)
    ALL_DONE_SIGNAL.set()

    if main_error and exception_in_threads:
        raise exception_in_threads from main_error
    elif main_error:
        raise main_error
    elif exception_in_threads:
        raise exception_in_threads
    else:
        sys.exit(0)


def stop_active_threads(threads):
    if not EXIT_SIGNAL.is_set():
        EXIT_SIGNAL.set()
    last_exception = None
    for unit in threads:
        try:
            unit['thread'].merge()
        except Exception as e:
            last_exception = e
    return last_exception


if __name__ == '__main__':
    main()
