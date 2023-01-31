""" python -m unittest tests.units.updater.test_updater """
import unittest
from unittest.mock import patch, Mock
from datetime import timedelta
from time import sleep

from lucky_bot.helpers.constants import TestException, UpdateDispatcherException
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, UPDATER_CYCLE, EXIT_SIGNAL
from lucky_bot.updater.updater import Updater
from lucky_bot.updater import UpdaterThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


@patch('lucky_bot.updater.updater.Updater.works')
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
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 1
        current_time = Updater._get_current_time()

        self.assertTrue(current_time.before_the_first_update)
        self.assertFalse(current_time.first_update)
        self.assertFalse(current_time.second_update)

    def test_after_the_first_update(self, fut, sut, dt):
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 12
        current_time = Updater._get_current_time()

        self.assertFalse(current_time.before_the_first_update)
        self.assertTrue(current_time.first_update)
        self.assertFalse(current_time.second_update)

    def test_after_the_second_update(self, fut, sut, dt):
        fut.return_value = 12
        sut.return_value = 18

        dt.now.return_value = 18
        current_time = Updater._get_current_time()

        self.assertFalse(current_time.before_the_first_update)
        self.assertFalse(current_time.first_update)
        self.assertTrue(current_time.second_update)


@patch('lucky_bot.updater.updater.datetime')
@patch('lucky_bot.updater.updater.second_update_time')
@patch('lucky_bot.updater.updater.first_update_time')
class TestUpdaterThreadTimeToWait(unittest.TestCase):
    expected = 3600 - 600 - 30 + 10

    def test_before_the_first_update(self, fut, sut, dt):
        fut.return_value = timedelta(hours=12)
        dt.now.return_value = timedelta(hours=11, minutes=10, seconds=30)

        result = UpdaterThread._time_to_wait()
        self.assertEqual(result, self.expected)

    def test_after_the_first_update(self, fut, sut, dt):
        fut.return_value = timedelta(hours=12)
        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=17, minutes=10, seconds=30)

        result = UpdaterThread._time_to_wait()
        self.assertEqual(result, self.expected)

    @patch('lucky_bot.updater.updater.next_day_time')
    def test_after_the_second_update(self, ndt, fut, sut, dt):
        fut.return_value = timedelta(days=1, hours=12)
        sut.return_value = timedelta(days=1, hours=18)
        ndt.return_value = timedelta(days=2, hours=0)
        dt.now.return_value = timedelta(days=1, hours=23, minutes=10, seconds=30)

        result = UpdaterThread._time_to_wait()
        self.assertEqual(result, self.expected)


@patch('lucky_bot.updater.updater.UpdaterThread._test_updater_cycle')
@patch('lucky_bot.updater.updater.update_dispatcher')
@patch('lucky_bot.updater.updater.datetime')
@patch('lucky_bot.updater.updater.second_update_time')
@patch('lucky_bot.updater.updater.first_update_time')
class TestUpdaterExecution(ThreadSmallTestTemplate):
    thread_class = UpdaterThread
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED
    other_signals = [UPDATER_CYCLE]

    def test_updater_normal_case(self, fut, sut, dt, dispatcher, updater_cycle):
        fut.return_value = timedelta(hours=12)
        dt.now.return_value = timedelta(hours=10)
        UPDATER_CYCLE.set()

        self.thread_obj.start()
        if not UPDATER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the updater has passed.')

        self.assertFalse(UPDATER_CYCLE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        dispatcher.clear_all_users_flags.assert_called_once()
        dispatcher.send_messages.assert_called_once()
        updater_cycle.assert_not_called()

        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=15)

        UPDATER_CYCLE.set()
        sleep(0.2)
        self.assertFalse(UPDATER_CYCLE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        self.assertEqual(dispatcher.clear_all_users_flags.call_count, 2)
        self.assertEqual(dispatcher.send_messages.call_count, 2)
        updater_cycle.assert_called_once()

        EXIT_SIGNAL.set()
        UPDATER_CYCLE.set()
        if not UPDATER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the updater has passed.')

        self.thread_obj.merge()
        updater_cycle.assert_called_once()

    def test_updater_exception_in_dispatcher(self, fut, sut, dt, dispatcher, updater_cycle):
        fut.return_value = timedelta(hours=12)
        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=15)
        dispatcher.send_messages.side_effect = [None, TestException('boom')]
        UPDATER_CYCLE.set()

        self.thread_obj.start()
        if not UPDATER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the updater has passed.')

        dispatcher.send_messages.assert_called_once()
        self.assertFalse(EXIT_SIGNAL.is_set())

        UPDATER_CYCLE.set()
        if not UPDATER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the updater has passed.')

        self.assertRaises(UpdateDispatcherException, self.thread_obj.merge)
        updater_cycle.assert_not_called()
