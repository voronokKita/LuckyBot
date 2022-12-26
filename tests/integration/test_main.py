""" python -m unittest tests.integration.test_main """
from time import sleep
import threading
import unittest

from lucky_bot.helpers.signals import ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL


class MainTestException(Exception):
    ...


class TestMain(unittest.TestCase):
    def setUp(self):
        import main
        self.main_thread = threading.Thread(target=main.main, name='main integrity thread')

    def tearDown(self):
        if not EXIT_SIGNAL:
            EXIT_SIGNAL.set()
        self.main_thread.join(10)

    def test_main_integrity(self):
        self.main_thread.start()

        if ALL_THREADS_ARE_GO.wait(5):
            EXIT_SIGNAL.set()
        else:
            raise MainTestException('The time to start the threads has passed.')

        if ALL_DONE_SIGNAL.wait(10):
            sleep(0.01)
            self.main_thread.join(10)
            self.assertFalse(self.main_thread.is_alive())
        else:
            raise MainTestException('The time to finish the work has passed.')
