"""
Flask Live Transcription Starter - Backend Server

This Flask server provides a WebSocket endpoint for live speech-to-text
powered by Deepgram's Live API. It proxies audio from the frontend to
Deepgram and streams back real-time transcription results.

Key Features:
- WebSocket endpoint: /live-stt/stream
- Accepts binary audio streams from frontend
- Returns real-time transcription results
- Serves built frontend from frontend/dist/
"""

import os
import json
import threading
from flask import Flask, request
from flask_sock import Sock
from flask_cors import CORS
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions
)
from dotenv import load_dotenv

# Load .env file (won't override existing environment variables)
load_dotenv(override=False)

# ============================================================================
# CONFIGURATION - Customize these values for your needs
# ============================================================================

# Default transcription model to use when none is specified
DEFAULT_MODEL = "nova-3"
DEFAULT_LANGUAGE = "en"
DEFAULT_PORT = 3000

# ============================================================================
# API KEY VALIDATION
# ============================================================================

def validate_api_key():
    """Validates that the Deepgram API key is configured"""
    api_key = os.environ.get("DEEPGRAM_API_KEY")

    if not api_key:
        print("\n" + "="*70)
        print("ERROR: Deepgram API key not found!")
        print("="*70)
        print("\nPlease set your API key using one of these methods:")
        print("\n1. Create a .env file (recommended):")
        print("   DEEPGRAM_API_KEY=your_api_key_here")
        print("\n2. Environment variable:")
        print("   export DEEPGRAM_API_KEY=your_api_key_here")
        print("\nGet your API key at: https://console.deepgram.com")
        print("="*70 + "\n")
        raise ValueError("DEEPGRAM_API_KEY environment variable is required")

    return api_key

# Validate on startup
API_KEY = validate_api_key()

# ============================================================================
# SETUP - Initialize Flask, WebSocket, and CORS
# ============================================================================

# Initialize Flask app - serve built frontend from frontend/dist/
app = Flask(__name__, static_folder="./frontend/dist", static_url_path="/")

# Enable CORS for development (allows Vite dev server to connect)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # In production, restrict to your domain
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize native WebSocket support
sock = Sock(app)

# ============================================================================
# HTTP ROUTES
# ============================================================================

@app.route("/")
def index():
    """Serve the main frontend HTML file"""
    return app.send_static_file("index.html")

# ============================================================================
# WEBSOCKET ENDPOINT - Live Transcription
# ============================================================================

@sock.route('/live-stt/stream')
def live_transcription(ws):
    """
    WebSocket endpoint for live speech-to-text transcription

    Query parameters:
    - model: Deepgram model (default: nova-3)
    - language: Language code (default: en)

    The client sends binary audio data and receives JSON messages with:
    - type: "Results" | "Metadata" | "Error"
    - transcript, is_final, confidence, words, etc.
    """
    print("Client connected to /live-stt/stream")

    # Get query parameters from request
    model = request.args.get('model', DEFAULT_MODEL)
    language = request.args.get('language', DEFAULT_LANGUAGE)

    # Initialize Deepgram connection
    deepgram_connection = None
    keep_alive_thread = None
    stop_keepalive = threading.Event()

    try:
        # Create Deepgram client with timeout configuration
        config = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        deepgram = DeepgramClient(API_KEY, config)

        # Configure live transcription options
        options = LiveOptions(
            model=model,
            language=language,
            smart_format=True,
        )

        # Create live connection
        deepgram_connection = deepgram.listen.live.v("1")

        # Set up Deepgram event handlers
        def on_open(self, open_event, **kwargs):
            """Handle Deepgram connection open"""
            print(f"Deepgram connection opened - model: {model}, language: {language}")

        def on_message(self, result, **kwargs):
            """Handle transcript results from Deepgram"""
            try:
                # Extract transcript from Deepgram response
                sentence = result.channel.alternatives[0].transcript

                if len(sentence) > 0:
                    # Format response according to live-stt contract
                    response = {
                        'type': 'Results',
                        'transcript': sentence,
                        'is_final': result.is_final if hasattr(result, 'is_final') else False,
                        'speech_final': result.speech_final if hasattr(result, 'speech_final') else False,
                    }

                    # Add optional fields if available
                    if hasattr(result.channel.alternatives[0], 'confidence'):
                        response['confidence'] = result.channel.alternatives[0].confidence

                    if hasattr(result.channel.alternatives[0], 'words') and result.channel.alternatives[0].words:
                        response['words'] = [
                            {
                                'word': word.word,
                                'start': word.start,
                                'end': word.end,
                                'confidence': word.confidence if hasattr(word, 'confidence') else None
                            }
                            for word in result.channel.alternatives[0].words
                        ]

                    if hasattr(result, 'duration'):
                        response['duration'] = result.duration

                    if hasattr(result, 'start'):
                        response['start'] = result.start

                    response['metadata'] = {
                        'model': model,
                        'language': language
                    }

                    # Send to client
                    ws.send(json.dumps(response))

            except Exception as e:
                print(f"Error processing Deepgram message: {e}")
                error_response = format_error_response('TRANSCRIPTION_FAILED', 'Error processing transcript')
                ws.send(json.dumps(error_response))

        def on_metadata(self, metadata, **kwargs):
            """Handle metadata from Deepgram"""
            try:
                response = {
                    'type': 'Metadata',
                    'request_id': metadata.request_id if hasattr(metadata, 'request_id') else None,
                    'model_info': {
                        'name': metadata.model_info.name if hasattr(metadata, 'model_info') else model,
                        'version': metadata.model_info.version if hasattr(metadata, 'model_info') and hasattr(metadata.model_info, 'version') else None
                    },
                    'created': metadata.created if hasattr(metadata, 'created') else None
                }

                ws.send(json.dumps(response))
            except Exception as e:
                print(f"Error processing metadata: {e}")

        def on_error(self, error, **kwargs):
            """Handle errors from Deepgram"""
            print(f"Deepgram error: {error}")
            error_response = format_error_response('CONNECTION_FAILED', 'Deepgram connection error')
            ws.send(json.dumps(error_response))

        def on_close(self, close_event, **kwargs):
            """Handle Deepgram connection close"""
            print("Deepgram connection closed")
            stop_keepalive.set()

        # Register event handlers
        deepgram_connection.on(LiveTranscriptionEvents.Open, on_open)
        deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        deepgram_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)
        deepgram_connection.on(LiveTranscriptionEvents.Close, on_close)

        # Start the Deepgram connection
        if deepgram_connection.start(options) is False:
            print("Failed to start Deepgram connection")
            error_response = format_error_response('CONNECTION_FAILED', 'Failed to start Deepgram connection')
            ws.send(json.dumps(error_response))
            return

        # Start keepalive thread
        def send_keepalive():
            while not stop_keepalive.is_set():
                try:
                    if deepgram_connection:
                        deepgram_connection.keep_alive()
                except Exception as e:
                    print(f"Keepalive error: {e}")
                    break
                stop_keepalive.wait(5)  # Send keepalive every 5 seconds

        keep_alive_thread = threading.Thread(target=send_keepalive, daemon=True)
        keep_alive_thread.start()

        print("WebSocket connection established, waiting for audio data...")

        # Main loop: receive audio from client and forward to Deepgram
        while True:
            data = ws.receive()

            if data is None:
                # Connection closed
                print("Client disconnected")
                break

            # Forward binary audio to Deepgram
            if isinstance(data, bytes):
                if deepgram_connection:
                    deepgram_connection.send(data)
            elif isinstance(data, str):
                # Handle text messages (could be control messages in the future)
                try:
                    message = json.loads(data)
                    message_type = message.get('type')

                    if message_type == 'KeepAlive':
                        # Client keepalive - just acknowledge
                        pass
                    elif message_type == 'CloseStream':
                        # Client requesting graceful close
                        print("Client requested stream close")
                        break
                    elif message_type == 'Finalize':
                        # Client requesting finalization
                        if deepgram_connection:
                            deepgram_connection.finish()
                except json.JSONDecodeError:
                    print(f"Received invalid JSON: {data}")
                except Exception as e:
                    print(f"Error processing control message: {e}")

    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
        try:
            error_response = format_error_response('CONNECTION_FAILED', 'WebSocket connection error')
            ws.send(json.dumps(error_response))
        except:
            pass

    finally:
        # Cleanup
        print("Cleaning up connection...")

        # Stop keepalive thread
        stop_keepalive.set()
        if keep_alive_thread:
            keep_alive_thread.join(timeout=1)

        # Close Deepgram connection
        if deepgram_connection:
            try:
                deepgram_connection.finish()
            except Exception as e:
                print(f"Error closing Deepgram connection: {e}")

        print("Connection cleanup complete")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_error_response(code, message):
    """
    Format error responses according to the live-stt contract

    Args:
        code: Error code from the contract
        message: Human-readable error message

    Returns:
        dict: Formatted error response
    """
    return {
        'type': 'Error',
        'error': {
            'type': 'TranscriptionError',
            'code': code,
            'message': message
        }
    }

# ============================================================================
# SERVER START
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    print("\n" + "=" * 70)
    print(f"🚀 Flask Live Transcription Server running at http://localhost:{port}")
    print(f"📦 Serving built frontend from frontend/dist")
    print(f"🔌 WebSocket endpoint: ws://localhost:{port}/live-stt/stream")
    print(f"🐞 Debug mode: {'ON' if debug else 'OFF'}")
    print("=" * 70 + "\n")

    # Run Flask app
    app.run(
        host=host,
        port=port,
        debug=debug
    )
