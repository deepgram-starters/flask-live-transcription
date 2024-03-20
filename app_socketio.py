import logging
from threading import Event
from typing import Optional

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)
from deepgram.clients.live.v1 import LiveClient
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

load_dotenv()

app_socketio = Flask("app_socketio")
# TODO: change this to the frontend URL
socketio = SocketIO(app_socketio, cors_allowed_origins=['http://127.0.0.1:8000'])

# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

# Initialize Deepgram client and connection
deepgram = DeepgramClient("", config)

# Track transcription state
transcribing = False
transcription_event = Event()

_dg_connection: Optional[LiveClient] = None


def set_dg_connection(dg_connection: Optional[LiveClient]):
    global _dg_connection
    _dg_connection = dg_connection


def get_dg_connection() -> Optional[LiveClient]:
    return _dg_connection


def configure_deepgram(dg_connection: LiveClient):
    options = LiveOptions(
        smart_format=True,
        language="en-US",
        encoding="linear16",
        channels=1,
        sample_rate=16000,
    )
    dg_connection.start(options)

    set_dg_connection(dg_connection)


def start_transcription_loop():
    try:
        global transcribing
        while transcribing:
            dg_connection = deepgram.listen.live.v("1")
            configure_deepgram(dg_connection)

            def on_message(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if len(transcript) > 0:
                    socketio.emit('transcription_update', {'transcription': transcript})

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            # Wait for the transcription to finish
            transcription_event.wait()
            transcription_event.clear()

            # Finish the microphone and Deepgram connection
            dg_connection.finish()
            logging.info("Transcription loop finished.")

    except Exception as e:
        logging.error(f"Error: {e}")


def on_disconnect():
    logging.info("Client disconnected")
    dg_connection = get_dg_connection()
    if dg_connection:
        dg_connection.finish()
        set_dg_connection(None)
        logging.info("Cleared listeners and set dg_connection to None")
    else:
        logging.info("No active dg_connection to disconnect from")


@socketio.on('disconnect')
def handle_disconnect():
    socketio.start_background_task(target=on_disconnect)


@socketio.on('toggle_transcription')
def toggle_transcription(data):
    global transcribing
    action = data.get('action')

    if action == 'start' and not transcribing:
        # Start transcription
        transcribing = True
        socketio.start_background_task(target=start_transcription_loop)
    elif action == 'stop' and transcribing:
        # Stop transcription
        transcribing = False
        transcription_event.set()


# WebSocket route to receive audio data from the client
@socketio.on('audio_stream')
def audio_stream(message):
    dg_connection = get_dg_connection()
    if message and dg_connection:
        get_dg_connection().send(message)


if __name__ == '__main__':
    logging.info("Starting SocketIO server.")
    # For some reason it does not work with port 5000
    socketio.run(app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5001)
