import json
import os
import unittest

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
