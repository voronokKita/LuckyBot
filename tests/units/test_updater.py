""" python -m unittest tests.units.test_updater """
from unittest.mock import patch

from lucky_bot.updater import UpdaterThread
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED

from tests.presets import ThreadTestTemplate


class TestUpdaterThreadBase(ThreadTestTemplate):
    thread_class = UpdaterThread
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def test_updater_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception')
    def test_updater_exception_case(self, test_exception):
        super().exception_case(test_exception)

    def test_updater_forced_merge(self, *args):
        super().forced_merge()
