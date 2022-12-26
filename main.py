import sys
from time import sleep

from lucky_bot.helpers.signals import (
    WEBHOOK_IS_RUNNING, INPUT_CONTROLLER_IS_RUNNING, UPDATER_IS_RUNNING,
    SENDER_IS_RUNNING, ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL,
)

from lucky_bot.webhook import WebhookThread
from lucky_bot.input_controller import InputControllerThread
from lucky_bot.updater import UpdaterThread
from lucky_bot.sender import SenderThread


THREADS = {}


def main():
    # run all the threads;
    webhook = WebhookThread()
    input_controller = InputControllerThread()
    updater = UpdaterThread()
    sender = SenderThread()

    webhook.start()
    input_controller.start()
    updater.start()
    sender.start()

    for thread in THREADS:
        thread()
        # TODO WEBHOOK_IS_RUNNING
        # TODO INPUT_CONTROLLER_IS_RUNNING
        # TODO UPDATER_IS_RUNNING
        # TODO SENDER_IS_RUNNING
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
    webhook.stop()
    input_controller.stop()
    updater.stop()
    sender.stop()
    sleep(0.1)

    ALL_DONE_SIGNAL.set()
    sys.exit(0)


if __name__ == '__main__':
    main()
