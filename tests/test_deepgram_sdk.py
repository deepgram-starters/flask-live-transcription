import os
import httpx
from dotenv import load_dotenv
import pytest
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import threading
import time

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

URL = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"

transcript_received_event = threading.Event()

def test_deepgram_live_transcription():
    assert DEEPGRAM_API_KEY is not None, "DEEPGRAM_API_KEY is not set"

    deepgram: DeepgramClient = DeepgramClient(DEEPGRAM_API_KEY)

    print("Deepgram client created", deepgram)

    dg_connection = deepgram.listen.live.v("1")

    def on_open(self, open, **kwargs):
        print(f"\n\n{open}\n\n")

    def on_message(self, result, **kwargs):
        print("Received message")
        sentence = result.channel.alternatives[0].transcript
        assert sentence is not None, "No transcript received"
        print(sentence)
        if sentence:
            transcript_received_event.set()

    def on_close(self, close, **kwargs):
        print(f"\n\n{close}\n\n")

    def on_error(self, error, **kwargs):
        print(f"\n\n{error}\n\n")

    dg_connection.on(LiveTranscriptionEvents.Open, on_open)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)

    options = LiveOptions(model="nova-2", language="en-US")

    if not dg_connection.start(options):
        print("Failed to start connection")
        return

    print("Connection started")

    try:
        with httpx.stream("GET", URL) as r:
            start_time = time.time()
            for data in r.iter_bytes():
                dg_connection.send(data)
                # Wait for the transcript or timeout after 10 seconds
                if transcript_received_event.wait(timeout=3):
                    break
                # Break the loop after a certain period to avoid an infinite loop
                if time.time() - start_time > 20:
                    break
    except Exception as e:
        pytest.fail(f"Failed to stream data: {e}")

    dg_connection.finish()

    print("Finished")
