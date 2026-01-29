"""
Flask Live Transcription Starter - Backend Server

Simple WebSocket proxy to Deepgram's Live STT API.
Forwards all messages (JSON and binary) bidirectionally between client and Deepgram.
"""

import os
import threading
from flask import Flask, request, jsonify
from flask_sock import Sock
from flask_cors import CORS
from urllib.parse import urlencode
import websocket
import toml
from dotenv import load_dotenv

# Load .env file (won't override existing environment variables)
load_dotenv(override=False)

# ============================================================================
# CONFIGURATION
# ============================================================================

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
# WEBSOCKET ENDPOINT
# ============================================================================

@sock.route('/stt/stream')
def live_transcription(ws):
    """
    WebSocket endpoint for live speech-to-text transcription
    Simple bidirectional proxy to Deepgram's Live STT API

    Query parameters:
    - model: Deepgram model (default: nova-3)
    - language: Language code (default: en)
    - encoding: Audio encoding (default: linear16)
    - sample_rate: Sample rate in Hz (default: 16000)
    - channels: Number of audio channels (default: 1)

    The client sends binary audio data and receives JSON transcription messages.
    """
    print("Client connected to /stt/stream")

    # Get query parameters from request
    model = request.args.get('model', DEFAULT_MODEL)
    language = request.args.get('language', DEFAULT_LANGUAGE)
    smart_format = request.args.get('smart_format', 'true')
    encoding = request.args.get('encoding', 'linear16')
    sample_rate = request.args.get('sample_rate', '16000')
    channels = request.args.get('channels', '1')

    print(f"STT Config - model: {model}, language: {language}, encoding: {encoding}, sample_rate: {sample_rate}, channels: {channels}")

    # Build Deepgram WebSocket URL with query parameters
    deepgram_params = {
        'model': model,
        'language': language,
        'smart_format': smart_format,
        'encoding': encoding,
        'sample_rate': sample_rate,
        'channels': channels
    }
    deepgram_url = f"wss://api.deepgram.com/v1/listen?{urlencode(deepgram_params)}"

    # Message counters for logging
    client_message_count = 0
    deepgram_message_count = 0
    stop_event = threading.Event()

    def on_deepgram_message(dg_ws, message):
        """Forward messages from Deepgram to client"""
        nonlocal deepgram_message_count
        deepgram_message_count += 1

        # Log every 10th message or non-binary messages
        if deepgram_message_count % 10 == 0 or isinstance(message, str):
            print(f"← Deepgram message #{deepgram_message_count}")

        try:
            ws.send(message)
        except Exception as e:
            print(f"Error forwarding to client: {e}")
            stop_event.set()

    def on_deepgram_error(dg_ws, error):
        """Handle Deepgram errors"""
        print(f"Deepgram error: {error}")
        stop_event.set()

    def on_deepgram_close(dg_ws, close_status_code, close_msg):
        """Handle Deepgram connection close"""
        print(f"Deepgram connection closed: {close_status_code} {close_msg}")
        stop_event.set()

    def on_deepgram_open(dg_ws):
        """Handle Deepgram connection open"""
        print("✓ Connected to Deepgram STT API")

    # Create WebSocket connection to Deepgram
    try:
        deepgram_ws = websocket.WebSocketApp(
            deepgram_url,
            header={
                'Authorization': f'Token {API_KEY}'
            },
            on_open=on_deepgram_open,
            on_message=on_deepgram_message,
            on_error=on_deepgram_error,
            on_close=on_deepgram_close
        )

        # Run Deepgram WebSocket in background thread
        dg_thread = threading.Thread(target=deepgram_ws.run_forever)
        dg_thread.daemon = True
        dg_thread.start()

        # Forward messages from client to Deepgram
        while not stop_event.is_set():
            try:
                # Receive message from client (with timeout)
                message = ws.receive(timeout=0.1)
                if message is None:
                    continue

                client_message_count += 1

                # Log every 100th binary message
                if client_message_count % 100 == 0:
                    print(f"→ Client message #{client_message_count}")

                # Forward to Deepgram
                if isinstance(message, bytes):
                    deepgram_ws.send(message, opcode=websocket.ABNF.OPCODE_BINARY)
                else:
                    deepgram_ws.send(message)

            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"Error in client message loop: {e}")
                    break

    except Exception as e:
        print(f"Error setting up STT connection: {e}")
        try:
            ws.close(1011, "Internal server error")
        except:
            pass
        return

    finally:
        # Cleanup
        print("Cleaning up STT connection")
        stop_event.set()
        try:
            deepgram_ws.close()
        except Exception as e:
            print(f"Error closing Deepgram connection: {e}")

        print("Client disconnected from /stt/stream")

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

    app.run(host=host, port=port, debug=debug)
