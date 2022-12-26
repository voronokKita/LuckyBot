from lucky_bot.helpers.signals import SENDER_IS_RUNNING


def sender_thread():
    SENDER_IS_RUNNING.set()
