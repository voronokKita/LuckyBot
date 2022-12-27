TREAD_RUNNING_TIMEOUT = 10


class TestException(Exception):
    ''' For testing purposes. '''

class MainError(Exception):
    ''' For a main.py '''

class ThreadException(Exception):
    ''' For the threads, except main. '''
