import logging
import os
import wave
import time
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    DeepgramClientOptions
)
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.WARN,  # Change to logging.INFO or logging.DEBUG for more verbose output
    options={"keepalive": "true"}
)

deepgram = DeepgramClient(API_KEY, config)

def initialize_deepgram_connection():
    # Initialize Deepgram client and connection
    dg_connection = deepgram.listen.live.v("1")

    def on_open(self, open, **kwargs):
        print(f"\n\n{open}\n\n")

    def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            print(result.channel.alternatives[0].transcript)

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
    return dg_connection

def send_audio_data(dg_connection, audio_file_path):
    with wave.open(audio_file_path, 'rb') as audio:
        chunk_size = 1024
        data = audio.readframes(chunk_size)
        while data:
            dg_connection.send(data)
            data = audio.readframes(chunk_size)
            time.sleep(0.1)  # Simulate real-time sending

if __name__ == '__main__':
    logging.info("Starting Deepgram connection.")
    dg_connection = initialize_deepgram_connection()

    # Path to your audio file
    audio_file_path = 'sample.wav'

    send_audio_data(dg_connection, audio_file_path)

    # Keep the script running to maintain the connection
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping script")
