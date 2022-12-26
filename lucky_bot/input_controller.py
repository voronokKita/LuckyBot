from lucky_bot.helpers.signals import INPUT_CONTROLLER_IS_RUNNING


def input_controller_thread():
    INPUT_CONTROLLER_IS_RUNNING.set()
