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
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import (
    ListenV1SocketClientResponse,
    ListenV1MediaMessage,
    ListenV1ControlMessage
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
DEFAULT_PORT = 8080

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

@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    """
    GET /api/metadata

    Returns metadata about this starter application from deepgram.toml
    Required for standardization compliance
    """
    try:
        import toml
        from flask import jsonify

        with open('deepgram.toml', 'r') as f:
            config = toml.load(f)

        if 'meta' not in config:
            return jsonify({
                'error': 'INTERNAL_SERVER_ERROR',
                'message': 'Missing [meta] section in deepgram.toml'
            }), 500

        return jsonify(config['meta']), 200

    except FileNotFoundError:
        return jsonify({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'deepgram.toml file not found'
        }), 500

    except Exception as e:
        print(f"Error reading metadata: {e}")
        return jsonify({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': f'Failed to read metadata from deepgram.toml: {str(e)}'
        }), 500

# ============================================================================
# WEBSOCKET ENDPOINT - Live Transcription
# ============================================================================

@sock.route('/stt/stream')
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
    print("Client connected to /stt/stream")

    # Get query parameters from request
    model = request.args.get('model', DEFAULT_MODEL)
    language = request.args.get('language', DEFAULT_LANGUAGE)

    # Initialize Deepgram client
    client = DeepgramClient(api_key=API_KEY)

    # Thread control
    stop_event = threading.Event()
    deepgram_connection = None
    deepgram_context = None

    try:
        # Create Deepgram live connection (returns a context manager)
        deepgram_context = client.listen.v1.connect(
            model=model,
            language=language,
            smart_format=True

        )
        # Enter the context manager to get the actual connection object
        deepgram_connection = deepgram_context.__enter__()

        # Set up Deepgram event handlers
        def on_open(open_event):
            """Handle Deepgram connection open"""
            print(f"Deepgram connection opened - model: {model}, language: {language}")

            # Notify client we're ready to receive audio
            ready_message = {
                'type': 'Ready',
                'message': 'Ready to receive audio'
            }
            try:
                ws.send(json.dumps(ready_message))
            except Exception as e:
                print(f"Error sending ready message: {e}")

        def on_message(result: ListenV1SocketClientResponse):
            """Handle transcript results from Deepgram"""
            try:
                # Check if this is a transcript response
                if hasattr(result, 'channel'):
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

                # Check if this is metadata
                elif hasattr(result, 'request_id'):
                    metadata_response = {
                        'type': 'Metadata',
                        'request_id': result.request_id if hasattr(result, 'request_id') else None,
                        'model_info': {
                            'name': result.model_info.name if hasattr(result, 'model_info') else model,
                            'version': result.model_info.version if hasattr(result, 'model_info') and hasattr(result.model_info, 'version') else None
                        } if hasattr(result, 'model_info') else {'name': model},
                        'created': result.created if hasattr(result, 'created') else None
                    }
                    ws.send(json.dumps(metadata_response))

            except Exception as e:
                print(f"Error processing Deepgram message: {e}")
                error_response = format_error_response('TRANSCRIPTION_FAILED', 'Error processing transcript')
                ws.send(json.dumps(error_response))

        def on_error(error):
            """Handle errors from Deepgram"""
            print(f"Deepgram error: {error}")
            error_response = format_error_response('CONNECTION_FAILED', 'Deepgram connection error')
            try:
                ws.send(json.dumps(error_response))
            except Exception as send_err:
                pass

        def on_close(close_event):
            """Handle Deepgram connection close"""
            print("Deepgram connection closed")
            stop_event.set()

        # Register event handlers
        deepgram_connection.on(EventType.OPEN, on_open)
        deepgram_connection.on(EventType.MESSAGE, on_message)
        deepgram_connection.on(EventType.ERROR, on_error)
        deepgram_connection.on(EventType.CLOSE, on_close)

        # Start listening to Deepgram in a background thread
        def listen_to_deepgram():
            try:
                deepgram_connection.start_listening()
            except Exception as e:
                print(f"Error in Deepgram listening thread: {e}")
                stop_event.set()

        deepgram_thread = threading.Thread(target=listen_to_deepgram, daemon=True)
        deepgram_thread.start()

        print("WebSocket connection established, waiting for audio data...")

        # Main loop: receive audio from client and forward to Deepgram
        while not stop_event.is_set():
            data = ws.receive(timeout=1)  # 1 second timeout to check stop_event

            if data is None:
                # Connection closed or timeout
                if stop_event.is_set():
                    break
                continue

            # Forward binary audio to Deepgram
            if isinstance(data, bytes):
                try:
                    deepgram_connection.send_media(ListenV1MediaMessage(data))
                except Exception as e:
                    print(f"Error sending audio to Deepgram: {e}")
                    break
            elif isinstance(data, str):
                # Handle text messages (control messages)
                try:
                    message = json.loads(data)
                    message_type = message.get('type')

                    if message_type == 'KeepAlive':
                        # Client keepalive - send to Deepgram
                        deepgram_connection.send_control(ListenV1ControlMessage(type="KeepAlive"))
                    elif message_type == 'CloseStream':
                        # Client requesting graceful close
                        print("Client requested stream close")
                        break
                    elif message_type == 'Finalize':
                        # Client requesting finalization
                        deepgram_connection.send_control(ListenV1ControlMessage(type="Finalize"))
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
        stop_event.set()

        # Close Deepgram connection
        if deepgram_connection:
            try:
                deepgram_connection.finish()
            except Exception as e:
                print(f"Error finishing Deepgram connection: {e}")

        # Exit the context manager
        if deepgram_context:
            try:
                deepgram_context.__exit__(None, None, None)
            except Exception as e:
                print(f"Error exiting context manager: {e}")

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
    print(f"🔌 WebSocket endpoint: ws://localhost:{port}/stt/stream")
    print(f"🐞 Debug mode: {'ON' if debug else 'OFF'}")
    print("=" * 70 + "\n")

    # Run Flask app
    app.run(
        host=host,
        port=port,
        debug=debug
    )
