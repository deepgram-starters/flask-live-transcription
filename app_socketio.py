import logging
from threading import Event
import os

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

load_dotenv()
API_KEY = os.getenv("DEEPGRAM_API_KEY")

app_socketio = Flask("app_socketio")
# # TODO: change this to the frontend URL
socketio = SocketIO(app_socketio, cors_allowed_origins=['http://127.0.0.1:8000'])

# # Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

# # Initialize Deepgram client and connection
deepgram = DeepgramClient(API_KEY, config)
dg_connection = deepgram.listen.live.v("1")

def on_open(self, open, **kwargs):
    print(f"Connection Open")

def on_message(self, result, **kwargs):
    print(f"Received message: {result.channel.alternatives[0]}")

def on_close(self, close, **kwargs):
        print(f"Connection Closed")

def on_error(self, error, **kwargs):
    print(f"Handled Error: {error}")

dg_connection.on(LiveTranscriptionEvents.Open, on_open)
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)

options = LiveOptions(
        model="nova-2",
        smart_format=True,
        # encoding="linear16",
        # channels=1,
        # sample_rate=16000,
    )

if dg_connection.start(options) is False:
    print("Failed to connect to Deepgram")


@socketio.on('audio_stream')
def handle_audio_stream(data):
    print('Received audio stream')
    dg_connection.send(data)
    # Handle the audio stream data here (e.g., send to a transcription service)

@socketio.on('toggle_transcription')
def toggle_transcription(data):
    print('Received toggle_transcription')
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

@socketio.on('connect')
def test_connect():
    print('Connected')
#     print('transcription_update', {'data': 'Connected'})


# # Track transcription state
transcribing = False
transcription_event = Event()


# def configure_deepgram():
#     print("Configuring deepgram")
#     options = LiveOptions(
#         smart_format=True,
#         language="en-US",
#         encoding="linear16",
#         channels=1,
#         sample_rate=16000,
#     )
#     dg_connection.start(options)
#     print("hello")
#     print("Started listening", dg_connection)
#     # set_dg_connection(dg_connection)


def start_transcription_loop():
    print("Starting transcription loop")
    try:
        global transcribing
        while transcribing:
            print("Waiting for transcription")
            # configure_deepgram()
            print(dg_connection)

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


# def on_disconnect():
#     logging.info("Client disconnected")
#     # dg_connection = get_dg_connection()
#     if dg_connection:
#         dg_connection.finish()
#         # set_dg_connection(None)
#         logging.info("Cleared listeners and set dg_connection to None")
#     else:
#         logging.info("No active dg_connection to disconnect from")


# @socketio.on('disconnect')
# def handle_disconnect():
#     socketio.start_background_task(target=on_disconnect)


# @socketio.on('toggle_transcription')
# def toggle_transcription(data):
#     global transcribing
#     action = data.get('action')

#     if action == 'start' and not transcribing:
#         # Start transcription
#         transcribing = True
#         socketio.start_background_task(target=start_transcription_loop)
#     elif action == 'stop' and transcribing:
#         # Stop transcription
#         transcribing = False
#         transcription_event.set()


# # WebSocket route to receive audio data from the client
# @socketio.on('audio_stream')
# def audio_stream(message):
#     print("Received audio stream")
#     # dg_connection = get_dg_connection()
#     # print(dg_connection)
#     if message and dg_connection:
#         dg_connection.send(message)


if __name__ == '__main__':
    logging.info("Starting SocketIO server.")
    # For some reason it does not work with port 5000
    socketio.run(app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5001)