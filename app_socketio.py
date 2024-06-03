import logging
import os
from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions
)

load_dotenv()

app_socketio = Flask("app_socketio")
socketio = SocketIO(app_socketio, cors_allowed_origins=['http://127.0.0.1:8000'])

API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

# # Initialize Deepgram client and connection
deepgram = DeepgramClient(API_KEY, config)
dg_connection = deepgram.listen.live.v("1")

def on_open(self, open, **kwargs):
    print(f"\n\n{open}\n\n")

def on_message(self, result, **kwargs):
    transcript = result.channel.alternatives[0].transcript
    if len(transcript) > 0:
        print(result.channel.alternatives[0].transcript)
        socketio.emit('transcription_update', {'transcription': transcript})

def on_close(self, close, **kwargs):
    print(f"\n\n{close}\n\n")

def on_error(self, error, **kwargs):
    print(f"\n\n{error}\n\n")

dg_connection.on(LiveTranscriptionEvents.Open, on_open)
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)

# Define the options for the live transcription
options = LiveOptions(model="nova-2", language="en-US")

if dg_connection.start(options) is False:
    print("Failed to start connection")
    exit()

@socketio.on('audio_stream')
def handle_audio_stream(data):
    print("audio data received")
    dg_connection.send(data)

@socketio.on('connect')
def server_connect():
    print('Client connected')

if __name__ == '__main__':
    logging.info("Starting SocketIO server.")
    socketio.run(app_socketio, debug=True, allow_unsafe_werkzeug=True, port=5001)