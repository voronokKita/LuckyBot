import sys
import threading
from time import sleep

from lucky_bot.helpers.constants import MainError
from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING, UPDATER_IS_RUNNING,
    SENDER_IS_RUNNING, ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL,
)
from lucky_bot.sender import SenderThread
from lucky_bot.updater import UpdaterThread
from lucky_bot.input_controller import InputControllerThread
from lucky_bot.webhook import WebhookThread


class MainAsThread(threading.Thread):
    ''' The main reason for this class is testing. '''
    exception = None

    def __str__(self):
        return 'main thread'

    def __int__(self):
        threading.Thread.__init__(self)

    def run(self):
        try:
            main()
        except Exception as e:
            self.exception = e

    def stop(self):
        if not EXIT_SIGNAL.is_set():
            EXIT_SIGNAL.set()
        threading.Thread.join(self, 1)
        if self.exception:
            raise self.exception


def main():
    # instantiate threads;
    sender = SenderThread()
    updater = UpdaterThread()
    input_controller = InputControllerThread()
    webhook = WebhookThread()

    threads = {
        sender: SENDER_IS_RUNNING,
        updater: UPDATER_IS_RUNNING,
        input_controller: INPUT_CONTROLLER_IS_RUNNING,
        webhook: WEBHOOK_IS_RUNNING,
    }

    # run all the threads;
    active_threads = []
    for thread in threads:
        thread.start()
        active_threads.append(thread)
        if threads[thread].wait(2):
            pass
        else:
            thread_loading_timeout(thread, active_threads)

    ALL_THREADS_ARE_GO.set()

    # wait for the exit signal;
    if EXIT_SIGNAL.wait():
        pass

    # done.
    finish_the_work(active_threads)


def thread_loading_timeout(thread, active_threads):
    EXIT_SIGNAL.set()
    sleep(0.1)
    msg = f'Threads running has failed: {thread} timeout.'
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
    last_exception = None
    for thread in threads:
        try:
            thread.stop()
        except Exception as e:
            last_exception = e
    return last_exception


if __name__ == '__main__':
    main()
