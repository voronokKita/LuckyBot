""" python -m unittest tests.units.test_controller """
from unittest.mock import patch

from lucky_bot.controller import ControllerThread
from lucky_bot.helpers.signals import CONTROLLER_IS_RUNNING, CONTROLLER_IS_STOPPED

from tests.presets import ThreadTestTemplate



'''
Case 1
/start -> responder -> 'hello message'

Case 2
/help -> responder -> 'help message'

Case 3
/add -> responder -> 'invitation message'
text -> parser insert data -> 'OK or ERROR message'

Case 4
/list -> responder select data -> 'list message'

Case 5
/note [n] > responder select data -> 'text message'

Case 6
/delete [n, n+1] -> responder delete data -> 'OK or ERROR message'

Case exception
some text or wrong command -> responder -> 'help message'

Case exception
some command after add/ -> execute command

Case sender exception
/delete_user -> responder delete user
'''

class TestControllerThreadBase(ThreadTestTemplate):
    thread_class = ControllerThread
    is_running_signal = CONTROLLER_IS_RUNNING
    is_stopped_signal = CONTROLLER_IS_STOPPED

    def test_controller_normal_start(self):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_controller_exception_case(self, test_exception):
        super().exception_case(test_exception)

    def test_controller_forced_merge(self, *args):
        super().forced_merge()

