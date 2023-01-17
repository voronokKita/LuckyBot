""" python -m unittest tests.units.test_receiver """
import unittest
from unittest.mock import patch, Mock

from lucky_bot.helpers.signals import (
    RECEIVER_IS_RUNNING, RECEIVER_IS_STOPPED,
    EXIT_SIGNAL, INCOMING_MESSAGE,
)
from lucky_bot.helpers.constants import (
    TestException, ReceiverException, FlaskException,
    REPLIT, ADDRESS, PORT, PROJECT_DIR,
    WEBHOOK_SECRET, WEBHOOK_ENDPOINT,
)
from lucky_bot.receiver import FLASK_APP
from lucky_bot.receiver import InputQueue
from lucky_bot.receiver import ReceiverThread

from tests.presets import ThreadTestTemplate, ThreadSmallTestTemplate


def mock_ngrok():
    tunnel = Mock()
    tunnel.public_url = 'http://0.0.0.0'
    ngrok = Mock()
    ngrok.connect.return_value = tunnel
    return ngrok


def mock_telebot():
    bot = Mock()
    bot.set_webhook.return_value = True
    return bot


def mock_serving():
    def start_server(self=None):
        EXIT_SIGNAL.wait()
    return start_server


@patch('lucky_bot.receiver.receiver.ReceiverThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.receiver.receiver.ReceiverThread._make_server', Mock())
@patch('lucky_bot.receiver.receiver.BOT', new_callable=mock_telebot)
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestReceiverThreadBase(ThreadTestTemplate):
    thread_class = ReceiverThread
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED
    signals = [INCOMING_MESSAGE]

    def tearDown(self):
        if self.thread_obj.server:
            self.thread_obj.server.socket.close()
        super().tearDown()

    def test_receiver_normal_start(self, *args):
        super().normal_case()

    @patch('lucky_bot.helpers.misc.ThreadTemplate._test_exception_after_signal')
    def test_receiver_normal_exception(self, test_exception, *args):
        super().exception_case(test_exception)

    def test_receiver_forced_merge(self, *args):
        super().forced_merge()


@patch('lucky_bot.receiver.receiver.ReceiverThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.receiver.receiver.ReceiverThread._make_server')
@patch('lucky_bot.receiver.receiver.ReceiverThread._set_webhook')
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestTunnel(ThreadSmallTestTemplate):
    thread_class = ReceiverThread
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED
    signals = [INCOMING_MESSAGE]

    def setUp(self):
        self.assertFalse(REPLIT)
        super().setUp()

    def test_receiver_tunnel_setup(self, ngrok, *args):
        self.thread_obj.start()
        if not RECEIVER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the receiver has passed.')

        ngrok.connect.assert_called_once_with(PORT, proto='http', bind_tls=True)
        tunnel = ngrok.connect()
        self.assertEqual(self.thread_obj.tunnel, tunnel)
        self.assertEqual(self.thread_obj.webhook_url, 'http://0.0.0.0' + WEBHOOK_ENDPOINT)
        self.assertTrue(self.thread_obj.serving)

        self.thread_obj.merge()
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertIsNone(self.thread_obj.tunnel)

    def test_receiver_tunnel_exception(self, ngrok, set_webhook, *args):
        ngrok.connect.side_effect = TestException('boom')
        self.thread_obj.start()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        ngrok.connect.assert_called_once()
        set_webhook.assert_not_called()
        self.assertIsNone(self.thread_obj.tunnel)

        self.assertRaises(ReceiverException, self.thread_obj.merge)
        ngrok.disconnect.assert_not_called()
        ngrok.kill.assert_not_called()


@patch('lucky_bot.receiver.receiver.ReceiverThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.receiver.receiver.ReceiverThread._make_server')
@patch('lucky_bot.receiver.receiver.BOT', new_callable=mock_telebot)
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestWebhook(ThreadSmallTestTemplate):
    thread_class = ReceiverThread
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED
    signals = [INCOMING_MESSAGE]

    def test_receiver_setting_webhook(self, ngrok, bot, *args):
        self.thread_obj.start()
        if not RECEIVER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the receiver has passed.')

        ngrok.connect.assert_called_once()
        bot.remove_webhook.assert_called_once()
        bot.set_webhook.assert_called_once_with(
            url='http://0.0.0.0'+WEBHOOK_ENDPOINT,
            max_connections=10,
            secret_token=WEBHOOK_SECRET
        )
        self.assertTrue(self.thread_obj.webhook)
        self.assertIsNotNone(self.thread_obj.webhook_url)
        self.assertTrue(self.thread_obj.serving)

        self.thread_obj.merge()
        self.assertEqual(bot.remove_webhook.call_count, 2)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.webhook_url)

    def test_receiver_webhook_exception(self, ngrok, bot, make_server, *args):
        bot.set_webhook.return_value = False

        self.thread_obj.start()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        ngrok.connect.assert_called_once()
        bot.remove_webhook.assert_called_once()
        bot.set_webhook.assert_called_once()
        make_server.assert_not_called()
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertFalse(self.thread_obj.webhook)
        self.assertRaises(ReceiverException, self.thread_obj.merge)


@patch('lucky_bot.receiver.receiver.ReceiverThread._start_server', new_callable=mock_serving)
@patch('lucky_bot.receiver.receiver.BOT', new_callable=mock_telebot)
@patch('lucky_bot.receiver.receiver.ngrok', new_callable=mock_ngrok)
class TestServer(ThreadSmallTestTemplate):
    thread_class = ReceiverThread
    is_running_signal = RECEIVER_IS_RUNNING
    is_stopped_signal = RECEIVER_IS_STOPPED
    signals = [INCOMING_MESSAGE]

    def setUp(self):
        self.assertIsNotNone(ADDRESS)
        self.assertIsNotNone(PORT)
        self.assertIsNotNone(FLASK_APP)
        super().setUp()

    def test_receiver_server(self, ngrok, bot, *args):
        from werkzeug.serving import BaseWSGIServer

        self.thread_obj.start()
        if not RECEIVER_IS_RUNNING.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to start the receiver has passed.')

        ngrok.connect.assert_called_once()
        bot.remove_webhook.assert_called_once()
        bot.set_webhook.assert_called_once()
        self.assertIsNotNone(self.thread_obj.server)
        self.assertIsInstance(self.thread_obj.server, BaseWSGIServer)
        self.assertTrue(self.thread_obj.serving)

        EXIT_SIGNAL.set()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        self.assertFalse(self.thread_obj.serving)
        self.assertIsNotNone(self.thread_obj.server)
        self.assertEqual(bot.remove_webhook.call_count, 2)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.webhook_url)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertIsNone(self.thread_obj.tunnel)

        self.thread_obj.merge()
        self.assertIsNone(self.thread_obj.server)

    @patch('lucky_bot.receiver.receiver.ReceiverThread._make_server')
    def test_receiver_making_server_exception(self, make_server, ngrok, bot, *args):
        make_server.side_effect = TestException('boom')

        self.thread_obj.start()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        bot.set_webhook.assert_called_once()
        ngrok.connect.assert_called_once()
        self.assertFalse(self.thread_obj.serving)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertIsNone(self.thread_obj.tunnel)
        self.assertEqual(bot.remove_webhook.call_count, 2)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.webhook_url)
        self.assertIsNone(self.thread_obj.server)
        self.assertRaises(ReceiverException, self.thread_obj.merge)

    @patch('lucky_bot.receiver.receiver.ReceiverThread._test_exception_after_serving')
    def test_receiver_starting_server_exception(self, start_serving, ngrok, bot, *args):
        start_serving.side_effect = TestException('boom')

        self.thread_obj.start()
        if not RECEIVER_IS_STOPPED.wait(10):
            self.thread_obj.merge()
            raise TestException('The time to stop the receiver has passed.')

        bot.set_webhook.assert_called_once()
        ngrok.connect.assert_called_once()
        self.assertFalse(self.thread_obj.serving)
        ngrok.disconnect.assert_called_once()
        ngrok.kill.assert_called_once()
        self.assertIsNone(self.thread_obj.tunnel)
        self.assertEqual(bot.remove_webhook.call_count, 2)
        self.assertFalse(self.thread_obj.webhook)
        self.assertIsNone(self.thread_obj.webhook_url)
        self.assertIsNotNone(self.thread_obj.server)

        self.assertRaises(ReceiverException, self.thread_obj.merge)
        self.assertIsNone(self.thread_obj.server)


@patch('lucky_bot.receiver.flask_config.InputQueue')
class TestFlaskApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = PROJECT_DIR / 'tests' / 'fixtures' / 'telegram_request.json'
        with open(fixture) as f:
            cls.telegram_request = f.read().strip()

    def setUp(self):
        FLASK_APP.config['ENV'] = 'development'
        FLASK_APP.config['TESTING'] = True
        FLASK_APP.config['DEBUG'] = True
        self.client = FLASK_APP.test_client()

    def tearDown(self):
        signals = [EXIT_SIGNAL, INCOMING_MESSAGE]
        [signal.clear() for signal in signals if signal.is_set()]
        FLASK_APP.config['ENV'] = 'production'
        FLASK_APP.config['TESTING'] = False
        FLASK_APP.config['DEBUG'] = False

    def test_flask_app_ping(self, *args):
        response = self.client.get('/ping')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'pong')

    def test_flask_app_normal_request(self, imq):
        response = self.client.post(
            WEBHOOK_ENDPOINT,
            headers={'Content-Type': 'application/json',
                     'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
            data=self.telegram_request.encode(),
        )
        self.assertEqual(response.status_code, 200)
        imq.add_message.assert_called_once()

    def test_flask_app_wrong_request(self, *args):
        response = self.client.post(WEBHOOK_ENDPOINT, data=r'junk')
        self.assertEqual(response.status_code, 400)

    @patch('lucky_bot.receiver.flask_config.get_message_data')
    def test_flask_app_get_msg_exception(self, get_message, *args):
        get_message.side_effect = TestException('boom')
        with self.assertRaises(FlaskException):
            response = self.client.post(WEBHOOK_ENDPOINT, data=r'junk')
        self.assertTrue(EXIT_SIGNAL.is_set())

    @patch('lucky_bot.receiver.flask_config.test_exception')
    def test_flask_app_save_msg_exception(self, test_exception, *args):
        test_exception.side_effect = TestException('boom')
        with self.assertRaises(FlaskException):
            response = self.client.post(
                WEBHOOK_ENDPOINT,
                headers={'Content-Type': 'application/json',
                         'X-Telegram-Bot-Api-Secret-Token': WEBHOOK_SECRET},
                data=self.telegram_request.encode(),
            )
        self.assertTrue(EXIT_SIGNAL.is_set())


class TestReceiverMessageQueue(unittest.TestCase):
    def setUp(self):
        InputQueue.set_up()

    def tearDown(self):
        InputQueue.tear_down()

    def test_output_queue_works(self):
        InputQueue.add_message('foo', 1)
        InputQueue.add_message('bar', 2)
        InputQueue.add_message('baz', 3)

        for message in ['foo', 'bar', 'baz']:
            msg_obj = InputQueue.get_first_message()
            self.assertIsNotNone(msg_obj, msg=message)
            self.assertEqual(msg_obj.data, message)
            InputQueue.delete_message(msg_obj)

        result = InputQueue.get_first_message()
        self.assertIsNone(result)
