import sys
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
        if threads[thread].wait(2):
            active_threads.append(thread)
        else:
            thread_loading_timeout(thread, active_threads)

    ALL_THREADS_ARE_GO.set()

    # wait for the exit signal;
    if EXIT_SIGNAL.wait():
        pass

    # finish the work;
    exception_in_threads = stop_the_threads(active_threads)

    ALL_DONE_SIGNAL.set()
    if exception_in_threads:
        raise exception_in_threads
    sys.exit(0)


def stop_the_threads(threads):
    last_exception = None
    for thread in threads:
        try:
            thread.stop()
        except Exception as e:
            last_exception = e
    return last_exception


def thread_loading_timeout(thread, active_threads):
    EXIT_SIGNAL.set()
    sleep(0.1)
    msg = f'Threads running has failed: {thread} timeout.'
    exception_in_threads = stop_the_threads(active_threads)
    if exception_in_threads:
        raise exception_in_threads from MainError(msg)
    else:
        raise MainError(msg)


if __name__ == '__main__':
    main()
