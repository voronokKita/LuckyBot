""" python -m unittest tests.integration.updater.test_updater_int """
from unittest.mock import patch
from datetime import timedelta
from time import sleep

from lucky_bot.helpers.constants import TestException, DatabaseException, UpdateDispatcherException
from lucky_bot.helpers.signals import UPDATER_IS_RUNNING, UPDATER_IS_STOPPED, UPDATER_CYCLE, EXIT_SIGNAL
from lucky_bot import MainDB
from lucky_bot.sender import OutputQueue
from lucky_bot.updater import UpdaterThread

from tests.presets import ThreadSmallTestTemplate


@patch('lucky_bot.updater.updater.UpdaterThread._test_updater_cycle')
@patch('lucky_bot.updater.updater.datetime')
@patch('lucky_bot.updater.updater.second_update_time')
@patch('lucky_bot.updater.updater.first_update_time')
class TestUpdaterWorks(ThreadSmallTestTemplate):
    thread_class = UpdaterThread
    is_running_signal = UPDATER_IS_RUNNING
    is_stopped_signal = UPDATER_IS_STOPPED

    def setUp(self):
        MainDB.set_up()
        OutputQueue.set_up()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        OutputQueue.tear_down()
        MainDB.tear_down()

    @patch('lucky_bot.updater.updater.next_day_time')
    def test_updater_normal_case(self, ndt, fut, sut, dt, updater_cycle):
        fut.return_value = timedelta(days=1, hours=12)
        sut.return_value = timedelta(days=1, hours=18)
        dt.now.return_value = timedelta(days=1, hours=13)
        MainDB.add_user(1)
        MainDB.add_note(1, 'hello')
        UPDATER_CYCLE.set()

        # 1st
        self.thread_obj.start()
        if not UPDATER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the updater has passed.')

        self.assertFalse(UPDATER_CYCLE.is_set(), msg='first')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='first')
        updater_cycle.assert_not_called()

        user_q1 = MainDB.get_user(1)
        self.assertTrue(user_q1.got_first_update)
        msg_q1 = OutputQueue.get_first_message()
        self.assertIsNotNone(msg_q1)
        OutputQueue.delete_message(msg_q1[0])

        # 2nd
        dt.now.return_value = timedelta(days=1,hours=19)
        ndt.return_value = timedelta(days=2, hours=0)
        UPDATER_CYCLE.set()
        sleep(0.5)
        self.assertFalse(UPDATER_CYCLE.is_set(), msg='cycle')
        self.assertFalse(EXIT_SIGNAL.is_set(), msg='cycle')
        updater_cycle.assert_called_once()

        user_q2 = MainDB.get_user(1)
        self.assertTrue(user_q2.got_second_update)
        self.assertIsNotNone(OutputQueue.get_first_message())

        # end
        EXIT_SIGNAL.set()
        UPDATER_CYCLE.set()
        if not UPDATER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the updater has passed.')

        self.thread_obj.merge()
        updater_cycle.assert_called_once()

    @patch('lucky_bot.updater.update_dispatcher.set_update_flag')
    def test_updater_exception_in_dispatcher(self, flag, fut, sut, dt, updater_cycle):
        fut.return_value = timedelta(hours=12)
        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=15)
        MainDB.add_user(2)
        MainDB.add_note(2, 'world')
        flag.side_effect = TestException('boom')

        self.thread_obj.start()
        if not UPDATER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the updater has passed.')

        self.assertTrue(EXIT_SIGNAL.is_set())
        self.assertFalse(UPDATER_CYCLE.is_set())
        flag.assert_called_once()
        updater_cycle.assert_not_called()

        self.assertRaises(UpdateDispatcherException, self.thread_obj.merge)
        self.assertTrue(UPDATER_CYCLE.is_set())
        self.assertIsNotNone(OutputQueue.get_first_message())

    @patch('lucky_bot.database.test_func2')
    def test_updater_exception_in_main_db(self, func, fut, sut, dt, updater_cycle):
        fut.return_value = timedelta(hours=12)
        sut.return_value = timedelta(hours=18)
        dt.now.return_value = timedelta(hours=15)

        self.thread_obj.start()
        if not UPDATER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the updater has passed.')

        MainDB.add_user(3)
        MainDB.add_note(3, 'foobar')
        func.side_effect = TestException('boom')

        UPDATER_CYCLE.set()
        if not UPDATER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the updater has passed.')

        self.assertRaises(DatabaseException, self.thread_obj.merge)
