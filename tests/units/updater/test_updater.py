""" python -m unittest tests.units.updater.test_updater """
import unittest
from unittest.mock import patch, Mock, MagicMock
from datetime import timedelta

from lucky_bot.updater import UpdaterThread
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED

from tests.presets import ThreadTestTemplate


@patch('lucky_bot.updater.updater.UpdaterThread.work_steps')
@patch('lucky_bot.updater.updater.UpdaterThread._time_to_wait', Mock(return_value=100))
class TestUpdaterThreadBase(ThreadTestTemplate):
    thread_class = UpdaterThread
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def test_updater_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_updater_exception_case(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_updater_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.updater.updater.datetime')
@patch('lucky_bot.updater.updater.second_update_time')
@patch('lucky_bot.updater.updater.first_update_time')
class TestUpdaterCurrentTime(unittest.TestCase):
    def test_before_the_first_update(self, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 1
        current_time = updater._get_current_time()

        self.assertTrue(current_time.before_the_first_update)
        self.assertFalse(current_time.first_update)
        self.assertFalse(current_time.second_update)

    def test_after_the_first_update(self, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 12
        current_time = updater._get_current_time()

        self.assertFalse(current_time.before_the_first_update)
        self.assertTrue(current_time.first_update)
        self.assertFalse(current_time.second_update)

    def test_after_the_second_update(self, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 18
        current_time = updater._get_current_time()

        self.assertFalse(current_time.before_the_first_update)
        self.assertFalse(current_time.first_update)
        self.assertTrue(current_time.second_update)


@patch('lucky_bot.updater.updater.datetime')
@patch('lucky_bot.updater.updater.second_update_time')
@patch('lucky_bot.updater.updater.first_update_time')
class TestUpdaterTimeToWait(unittest.TestCase):
    expected = 3600 - 600 - 30 + 10

    def test_before_the_first_update(self, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = timedelta(hours=12)
        dt.now.return_value = timedelta(hours=11, minutes=10, seconds=30)

        result = updater._time_to_wait()
        self.assertEqual(result, self.expected)

    def test_after_the_first_update(self, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = timedelta(hours=12)
        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=17, minutes=10, seconds=30)

        result = updater._time_to_wait()
        self.assertEqual(result, self.expected)

    @patch('lucky_bot.updater.updater.next_day_time')
    def test_after_the_second_update(self, ndt, fut, sut, dt):
        updater = UpdaterThread()
        fut.return_value = timedelta(days=1, hours=12)
        sut.return_value = timedelta(days=1, hours=18)
        ndt.return_value = timedelta(days=2, hours=0)
        dt.now.return_value = timedelta(days=1, hours=23, minutes=10, seconds=30)

        result = updater._time_to_wait()
        self.assertEqual(result, self.expected)
