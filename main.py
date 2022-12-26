import sys
from time import sleep

from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING, UPDATER_IS_RUNNING,
    SENDER_IS_RUNNING, ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL,
)

from lucky_bot.receiver.webhook import webhook_thread
from lucky_bot.receiver.input_controller import input_controller_thread
from lucky_bot.updater.updater import updater_thread
from lucky_bot.sender.sender import sender_thread


THREADS = {
    webhook_thread: WEBHOOK_IS_RUNNING,
    input_controller_thread: INPUT_CONTROLLER_IS_RUNNING,
    updater_thread: UPDATER_IS_RUNNING,
    sender_thread: SENDER_IS_RUNNING
}


def main():
    # run all the threads;
    for thread in THREADS:
        thread()
        if THREADS[thread].wait(2):
            pass
        else:
            EXIT_SIGNAL.set()
            sleep(0.1)
            raise Exception('Threads running has failed.')

    ALL_THREADS_ARE_GO.set()

    # wait for the exit signal;
    if EXIT_SIGNAL.wait():
        pass

    # finish the work;
    ALL_DONE_SIGNAL.set()
    sys.exit(0)


if __name__ == '__main__':
    main()
