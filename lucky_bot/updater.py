from lucky_bot.helpers.signals import UPDATER_IS_RUNNING


def updater_thread():
    UPDATER_IS_RUNNING.set()
