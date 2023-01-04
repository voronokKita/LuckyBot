import sys
import signal
import threading

from lucky_bot.helpers.constants import MainException, TREAD_RUNNING_TIMEOUT
from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
    exit_signal,
)
from lucky_bot.sender import SenderThread
from lucky_bot.updater import UpdaterThread
from lucky_bot.controller import ControllerThread
from lucky_bot.webhook import WebhookThread

import logging
from logs.config import console, event, clear_old_logs
logger = logging.getLogger(__name__)


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
    console('I woke up (*・ω・)ﾉ')
    event.info('[>>> START >>>')

    # instantiate threads;
    sender = SenderThread()
    updater = UpdaterThread()
    controller = ControllerThread()
    webhook = WebhookThread()

    threads = [
        {'thread': sender, 'running': SENDER_IS_RUNNING},
        {'thread': updater, 'running': UPDATER_IS_RUNNING},
        {'thread': controller, 'running': CONTROLLER_IS_RUNNING},
        {'thread': webhook, 'running': WEBHOOK_IS_RUNNING},
    ]

    # run all the threads;
    active_threads = run_the_threads(threads)
    console('all work has started (´｡• ω •｡`)')
    event.info('normal start')
    ALL_THREADS_ARE_GO.set()

    # just sleep and wait for the exit signal;
    if EXIT_SIGNAL.wait():
        console('shutting down...')
        event.info('exit signal')
        pass

    # done.
    finish_the_work(active_threads)


def run_the_threads(threads):
    active_threads = []
    for unit in threads:
        console(f'start the {unit["thread"]}')
        unit['thread'].start()
        active_threads.append(unit)

        if unit['running'].wait(TREAD_RUNNING_TIMEOUT):
            if EXIT_SIGNAL.is_set():
                thread_loading_interrupted(active_threads)
        else:
            thread_loading_timeout(unit['thread'], active_threads)

    del threads
    return active_threads


def thread_loading_timeout(thread, active_threads):
    console(f'{thread} loading timeout, shutting down...')
    event.warning(f'{thread} loading timeout')

    EXIT_SIGNAL.set()
    main_msg = f'Failed to start the threads: {thread} timeout.'
    finish_the_work(active_threads, MainException(main_msg))


def thread_loading_interrupted(active_threads):
    console('exit signal, shutting down...')
    event.warning('exit signal is set')

    main_msg = 'Failed to start the threads: exit signal.'
    finish_the_work(active_threads, MainException(main_msg))


def finish_the_work(active_threads, main_exec=None):
    exception_in_threads = stop_active_threads(active_threads)
    ALL_DONE_SIGNAL.set()
    console('go to sleep (´-ω-｀)…zZZ')
    event.info('xxx STOP xxx]')

    if main_exec and exception_in_threads:
        raise exception_in_threads from main_exec
    elif main_exec:
        raise main_exec
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
            msg = f'exception in {unit["thread"]}'
            logger.exception(msg)
            event.error(msg)
            console(msg)
            last_exception = e
    return last_exception


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_signal)
    signal.signal(signal.SIGTSTP, exit_signal)
    clear_old_logs()
    main()
