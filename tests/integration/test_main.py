""" python -m unittest tests.integration.test_main """
from time import sleep
import threading
import unittest

from lucky_bot.helpers.signals import ALL_THREADS_ARE_GO, EXIT_SIGNAL, ALL_DONE_SIGNAL


class TestMain(unittest.TestCase):
    def testit(self):
        import main

        m = threading.Thread(target=main.main, name='main integrity thread')
        m.start()

        if ALL_THREADS_ARE_GO.wait(5):
            EXIT_SIGNAL.set()
        else:
            self._stop_the_thread(m)
            raise Exception('The time to start the threads has passed.')

        if ALL_DONE_SIGNAL.wait(5):
            sleep(0.1)
            pass
        else:
            self._stop_the_thread(m)
            raise Exception('The time to finish the work has passed.')

        self._stop_the_thread(m)

    @staticmethod
    def _stop_the_thread(thread):
        if not EXIT_SIGNAL:
            EXIT_SIGNAL.set()
        thread.join(10)


if __name__ == '__main__':
    import sys
    import pathlib

    base_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    if str(base_dir) not in sys.path:
        sys.path.append(str(base_dir))

    unittest.main()
