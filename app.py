from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
import logging
from threading import Event
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

# Set up client configuration
config = DeepgramClientOptions(
    verbose=logging.DEBUG,
    options={"keepalive": "true"}
)

# Initialize Deepgram client and connection
deepgram = DeepgramClient("", config)
dg_connection = deepgram.listen.live.v("1")

# Track transcription state
transcribing = False
transcription_event = Event()

def configure_deepgram():
    options = LiveOptions(
        smart_format=True,
        language="en-US",
        encoding="linear16",
        channels=1,
        sample_rate=16000,
    )
    dg_connection.start(options)

def start_microphone():
    microphone = Microphone(dg_connection.send)
    microphone.start()
    return microphone

def start_transcription_loop():
    try:
        global transcribing
        while transcribing:
            configure_deepgram()

            # Open a microphone stream
            microphone = start_microphone()

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
    global dg_connection
    if dg_connection:
        dg_connection.finish()
        dg_connection = None
        logging.info("Cleared listeners and set dg_connection to None")
    else:
        logging.info("No active dg_connection to disconnect from")

@app.route('/')
def index():
    return render_template('index.html')

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
    socketio.run(app, debug=True)
