import unittest
import threading
from unittest.mock import patch

from deepgram.core import ApiError
import app as starter


class SdkRedactionTest(unittest.TestCase):
    class Socket:
        def __init__(self):
            self.messages = []
            self.closed = None

        def send(self, message):
            self.messages.append(message)

        def close(self, code, reason):
            self.closed = (code, reason)

    def test_api_error_redacts_authorization_value(self):
        marker = "synthetic-api-key"
        error = ApiError(headers={"Authorization": f"Token {marker}"})

        self.assertNotIn(marker, str(error))

    def test_invalid_websocket_numeric_parameters_close_with_error(self):
        class Socket:
            closed = None

            def close(self, code, reason):
                self.closed = (code, reason)

        socket = Socket()
        with starter.app.test_request_context('/api/live-transcription?sample_rate=abc'):
            with patch.object(starter, 'validate_ws_token', return_value='access_token.test'):
                # Flask-Sock's view wrapper requires a real WSGI WebSocket; call its
                # enclosed handler to exercise the route's parameter validation.
                handler = starter.app.view_functions['live_transcription'].__closure__[0].cell_contents
                handler(socket)

        self.assertEqual(socket.closed, (1008, 'sample_rate and channels must be integers'))

    def test_connection_failure_reaches_browser_without_exception_text(self):
        socket = self.Socket()
        stop_event = threading.Event()
        error = Exception('Authorization: Token secret-key')

        starter._forward_connection_failed(socket, error, stop_event)

        self.assertEqual(socket.messages, [
            '{"type": "Error", "description": "Deepgram rejected the connection (HTTP 500)", "code": "CONNECTION_FAILED", "status": 500}'
        ])
        self.assertEqual(socket.closed, (3000, 'Deepgram connection failed'))
        self.assertTrue(stop_event.is_set())

    def test_handshake_failure_sends_connection_failed_before_close(self):
        class HandshakeError(Exception):
            status_code = 403

        socket = self.Socket()
        with starter.app.test_request_context('/api/live-transcription?model=unsupported'):
            with patch.object(starter, 'validate_ws_token', return_value='access_token.test'):
                with patch.object(starter.deepgram.listen.v1, 'connect', side_effect=HandshakeError()):
                    handler = starter.app.view_functions['live_transcription'].__closure__[0].cell_contents
                    handler(socket)

        self.assertEqual(socket.messages, [
            '{"type": "Error", "description": "Deepgram rejected the connection (HTTP 403)", "code": "CONNECTION_FAILED", "status": 403}'
        ])
        self.assertEqual(socket.closed, (3000, 'Deepgram connection failed'))
