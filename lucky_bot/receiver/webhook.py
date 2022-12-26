from lucky_bot.helpers.signals import WEBHOOK_IS_RUNNING

def webhook_thread():
    WEBHOOK_IS_RUNNING.set()
