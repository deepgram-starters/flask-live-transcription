import logging
from threading import Event
from typing import Optional

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from deepgram.clients.live.v1 import LiveClient
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

load_dotenv()

app = Flask(__name__)
# TODO: change this to the frontend URL
socketio = SocketIO(app, cors_allowed_origins=['http://127.0.0.1:8000', 'http://localhost:8000'])

# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.DEBUG,
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


def start_microphone(dg_connection: LiveClient):
    microphone = Microphone(dg_connection.send)
    microphone.start()
    return microphone


def start_transcription_loop():
    try:
        global transcribing
        while transcribing:
            dg_connection = deepgram.listen.live.v("1")
            configure_deepgram(dg_connection)

            # Open a microphone stream
            microphone = start_microphone(dg_connection)

            def on_message(self, result, **kwargs):
                transcript = result.channel.alternatives[0].transcript
                if len(transcript) > 0:
                    socketio.emit('transcription_update', {'transcription': transcript})

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            # Wait for the transcription to finish
            transcription_event.wait()
            transcription_event.clear()

            # Finish the microphone and Deepgram connection
            microphone.finish()
            dg_connection.finish()
            logging.info("Transcription loop finished.")

    except Exception as e:
        logging.error(f"Error: {e}")


def reconnect():
    try:
        logging.info("Reconnecting to Deepgram...")
        new_dg_connection = deepgram.listen.live.v("1")

        # Configure and start the new Deepgram connection
        configure_deepgram(new_dg_connection)

        logging.info("Reconnected to Deepgram successfully.")
        return new_dg_connection

    except Exception as e:
        logging.error(f"Reconnection failed: {e}")
        return None


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


if __name__ == '__main__':
    logging.info("Starting SocketIO server.")
    # For some reason we need to change the port sometimes
    # TODO make it back to 5000 (here and in js)
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5005)
