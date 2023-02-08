import sys
import signal
import threading

from lucky_bot.helpers.constants import (
    MainException, TREAD_RUNNING_TIMEOUT,
    ERRORS_TOTAL, TESTING,
)
from lucky_bot.helpers.signals import (
    RECEIVER_IS_RUNNING, CONTROLLER_IS_RUNNING,
    UPDATER_IS_RUNNING, SENDER_IS_RUNNING,
    ALL_THREADS_ARE_GO, ALL_DONE_SIGNAL, EXIT_SIGNAL,
    exit_signal,
)
from lucky_bot.sender import SenderThread
from lucky_bot.updater import UpdaterThread
from lucky_bot.controller import ControllerThread
from lucky_bot.receiver import ReceiverThread

import logging
logger = logging.getLogger(__name__)
from logs import Log, clear_old_logs


class MainAsThread(threading.Thread):
    """ The main reason for this class is testing. """
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
    Log.console('I woke up (*・ω・)ﾉ')
    Log.info('[>>> START >>>', console=False)

    # instantiate threads;
    sender = SenderThread()
    updater = UpdaterThread()
    controller = ControllerThread()
    receiver = ReceiverThread()

    threads = [
        {'thread': sender, 'running': SENDER_IS_RUNNING},
        {'thread': updater, 'running': UPDATER_IS_RUNNING},
        {'thread': controller, 'running': CONTROLLER_IS_RUNNING},
        {'thread': receiver, 'running': RECEIVER_IS_RUNNING},
    ]

    # run all the threads;
    active_threads = run_the_threads(threads)
    Log.console('all work has started (´｡• ω •｡`)')
    Log.info('normal start', console=False)
    ALL_THREADS_ARE_GO.set()

    # just sleep and wait for the exit signal;
    if EXIT_SIGNAL.wait():
        Log.console('shutting down...')
        Log.info('exit signal', console=False)

    # done.
    finish_the_work(active_threads)


def run_the_threads(threads):
    active_threads = []
    for unit in threads:
        Log.console(f'start the {unit["thread"]}')

        unit['thread'].start()
        active_threads.append(unit)

        if unit['running'].wait(TREAD_RUNNING_TIMEOUT):
            if EXIT_SIGNAL.is_set():
                thread_loading_interrupted(active_threads)
            else:
                pass
        else:
            thread_loading_timeout(unit['thread'], active_threads)

    return active_threads


def thread_loading_timeout(thread, active_threads):
    Log.console(f'main: {thread} loading timeout, shutting down...')
    Log.error(f'{thread} loading timeout', console=False)

    EXIT_SIGNAL.set()
    main_msg = f'Failed to start the threads: {thread} timeout.'
    finish_the_work(active_threads, MainException(main_msg))


def thread_loading_interrupted(active_threads):
    Log.console('exit signal, shutting down...')
    Log.warning('exit signal is set', console=False)

    main_msg = 'Failed to start the threads: exit signal.'
    finish_the_work(active_threads, MainException(main_msg))


def finish_the_work(active_threads, main_exec=None):
    exception_in_threads = stop_active_threads(active_threads)
    Log.console('go to sleep (´-ω-｀)…zZZ')
    Log.info('xxx STOP xxx]', console=False)

    try:
        if main_exec and exception_in_threads:
            raise exception_in_threads from main_exec
        elif exception_in_threads:
            raise exception_in_threads
        elif main_exec:
            raise main_exec
        else:
            pass
    except Exception as exc:
        if not TESTING:
            count_total_errors()
        raise exc
    else:
        # important
        sys.exit(0)
    finally:
        ALL_DONE_SIGNAL.set()


def stop_active_threads(threads):
    if not EXIT_SIGNAL.is_set():
        EXIT_SIGNAL.set()
    last_exception = None
    for unit in threads:
        try:
            unit['thread'].merge()
        except Exception as exc:
            msg = f'main: exception in {unit["thread"]}'
            logger.exception(msg)
            Log.error(msg, console=True)
            last_exception = exc
    return last_exception


def count_total_errors():
    try:
        errors_total = 0
        with ERRORS_TOTAL.open('r') as f:
            errors_total = int(f.read().strip())

        errors_total += 1

        with ERRORS_TOTAL.open('w') as f:
            f.write(errors_total)
    except Exception:
        pass


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_signal)
    signal.signal(signal.SIGTSTP, exit_signal)
    clear_old_logs()
    main()
