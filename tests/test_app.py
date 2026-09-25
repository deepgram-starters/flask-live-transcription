import json
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("DEEPGRAM_API_KEY", "test-key")

import app


class FakeWebSocket:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class LiveTranscriptionTests(unittest.TestCase):
    def test_untyped_deepgram_error_reaches_browser_as_error(self):
        websocket = FakeWebSocket()

        app._forward_to_browser(websocket, None)

        self.assertEqual(
            json.loads(websocket.messages[0]),
            {"type": "Error", "description": "Deepgram transcription error"},
        )

    def test_interim_results_are_disabled_by_default(self):
        self.assertFalse(app._query_bool({}, "interim_results", False))

    def test_interim_results_allow_explicit_opt_in(self):
        self.assertTrue(app._query_bool({"interim_results": "true"}, "interim_results", False))

    def test_connection_failure_forwards_safe_http_status(self):
        websocket = FakeWebSocket()
        error = SimpleNamespace(response=SimpleNamespace(status_code=401))

        app._forward_connection_failure(websocket, error)

        self.assertEqual(
            json.loads(websocket.messages[0]),
            {
                "type": "Error",
                "code": "CONNECTION_FAILED",
                "description": "Deepgram rejected the connection (HTTP 401)",
            },
        )

    def test_provider_error_preserves_description(self):
        websocket = FakeWebSocket()
        stop_event = app.threading.Event()

        app._forward_provider_error(
            websocket,
            SimpleNamespace(description="provider rejected the stream"),
            stop_event,
        )

        self.assertEqual(
            json.loads(websocket.messages[0]),
            {"type": "Error", "description": "provider rejected the stream"},
        )
        self.assertTrue(stop_event.is_set())
