"""
Flask Live Transcription Starter - Backend Server

Simple WebSocket proxy to Deepgram's Live STT API.
Forwards all messages (JSON and binary) bidirectionally between client and Deepgram.

API Endpoints:
- WS /api/live-transcription - WebSocket endpoint for live transcription
- GET /api/session - JWT session token endpoint
- GET /api/metadata - Returns metadata from deepgram.toml
"""

import functools
import os
import secrets
import threading
import time

import jwt
from flask import Flask, request, jsonify, send_from_directory
from flask_sock import Sock
from flask_cors import CORS
from simple_websocket import Server as _WsServer
import json
import toml
from dotenv import load_dotenv

from deepgram import DeepgramClient
from deepgram.core.events import EventType

# Monkey-patch simple-websocket to echo back the access_token.* subprotocol.
# flask-sock uses simple-websocket's Server class for the WebSocket handshake.
# By default, Server.choose_subprotocol only accepts subprotocols that are in a
# static allow-list, which doesn't work for dynamic JWT-bearing subprotocols.
# This override makes the server echo back any access_token.* subprotocol so the
# client receives the Sec-WebSocket-Protocol response header it expects.
_original_choose_subprotocol = _WsServer.choose_subprotocol


def _choose_subprotocol_with_token(self, ws_request):
    for proto in ws_request.subprotocols:
        if proto.startswith("access_token."):
            return proto
    return _original_choose_subprotocol(self, ws_request)


_WsServer.choose_subprotocol = _choose_subprotocol_with_token

# Load .env file (won't override existing environment variables)
load_dotenv(override=False)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MODEL = "nova-3"
DEFAULT_LANGUAGE = "en"

# Server configuration
CONFIG = {
    "port": int(os.environ.get("PORT", 8081)),
    "host": os.environ.get("HOST", "0.0.0.0"),
}

# ============================================================================
# SESSION AUTH - JWT tokens with rate limiting for production security
# ============================================================================

SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
JWT_EXPIRY = 3600  # 1 hour


def validate_ws_token():
    """Validates JWT from Sec-WebSocket-Protocol: access_token.<jwt> header."""
    protocol_header = request.headers.get("Sec-WebSocket-Protocol", "")
    protocols = [p.strip() for p in protocol_header.split(",")]
    token_proto = next((p for p in protocols if p.startswith("access_token.")), None)
    if not token_proto:
        return None
    token = token_proto[len("access_token."):]
    try:
        jwt.decode(token, SESSION_SECRET, algorithms=["HS256"])
        return token_proto
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


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

# One SDK client, reused across connections; the browser never sees the API key.
deepgram = DeepgramClient(api_key=API_KEY)


def _forward_to_browser(ws, message):
    """Forward one Deepgram message to the browser: bytes as binary, models as JSON."""
    try:
        if isinstance(message, (bytes, bytearray)):
            ws.send(bytes(message))
        elif isinstance(message, dict):
            ws.send(json.dumps(message))
        elif hasattr(message, "model_dump_json"):
            ws.send(message.model_dump_json())
        else:
            ws.send(json.dumps({"type": getattr(message, "type", "Unknown")}))
    except Exception as e:
        print(f"Error forwarding to browser: {e}")

# ============================================================================
# SETUP - Initialize Flask, WebSocket, and CORS
# ============================================================================

# Initialize Flask app (API server only)
app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app)

# Initialize native WebSocket support
sock = Sock(app)

# ============================================================================
# SESSION ROUTES - Auth endpoints (unprotected)
# ============================================================================

@app.route("/", methods=["GET"])
def serve_index():
    """Serve the built frontend index.html."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
    if not os.path.isfile(os.path.join(frontend_dir, "index.html")):
        return "Frontend not built. Run make build first.", 404
    return send_from_directory(frontend_dir, "index.html")


@app.route("/api/session", methods=["GET"])
def get_session():
    """Issues a JWT for session authentication."""
    token = jwt.encode(
        {"iat": int(time.time()), "exp": int(time.time()) + JWT_EXPIRY},
        SESSION_SECRET,
        algorithm="HS256",
    )
    return jsonify({"token": token})


# ============================================================================
# HTTP ROUTES
# ============================================================================

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

@sock.route('/api/live-transcription')
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
    # Validate JWT from WebSocket subprotocol
    valid_proto = validate_ws_token()
    if not valid_proto:
        ws.close(4401, "Unauthorized")
        return

    print("Client connected to /api/live-transcription")

    # Get query parameters from request
    model = request.args.get('model', DEFAULT_MODEL)
    language = request.args.get('language', DEFAULT_LANGUAGE)
    smart_format = request.args.get('smart_format', 'true').lower() == 'true'
    encoding = request.args.get('encoding', 'linear16')
    sample_rate = int(request.args.get('sample_rate', '16000'))
    channels = int(request.args.get('channels', '1'))

    print(f"STT Config - model: {model}, language: {language}, encoding: {encoding}, sample_rate: {sample_rate}, channels: {channels}")

    stop_event = threading.Event()

    # Bridge browser <-> Deepgram Live STT through the official SDK (listen.v1).
    try:
        with deepgram.listen.v1.connect(
            model=model,
            language=language,
            smart_format=smart_format,
            encoding=encoding,
            sample_rate=sample_rate,
            channels=channels,
        ) as connection:
            connection.on(EventType.MESSAGE, lambda m: _forward_to_browser(ws, m))
            connection.on(EventType.CLOSE, lambda _: stop_event.set())
            connection.on(EventType.ERROR, lambda e: (print(f"Deepgram error: {e}"), stop_event.set()))

            # start_listening() blocks, so run it in a background thread while the
            # main thread forwards browser audio/control messages to Deepgram.
            threading.Thread(target=connection.start_listening, daemon=True).start()
            print("Ready to forward messages")

            while not stop_event.is_set():
                try:
                    message = ws.receive(timeout=0.1)
                except Exception:
                    break  # client disconnected
                if message is None:
                    continue

                # Browser audio arrives as binary; forward it as media.
                if isinstance(message, (bytes, bytearray)):
                    connection.send_media(bytes(message))
                    continue

                # Text frames are JSON control messages from the browser.
                try:
                    data = json.loads(message)
                except (ValueError, TypeError):
                    print("Ignoring non-JSON message from client")
                    continue

                msg_type = data.get("type")
                try:
                    if msg_type == "KeepAlive":
                        connection.send_keep_alive()
                    elif msg_type == "Finalize":
                        connection.send_finalize()
                    elif msg_type == "CloseStream":
                        connection.send_close_stream()
                    else:
                        print(f"Ignoring unknown client message type: {msg_type}")
                except Exception as e:
                    print(f"Error forwarding to Deepgram: {e}")

    except Exception as e:
        print(f"Error setting up STT connection: {e}")
        try:
            ws.close(1011, "Internal server error")
        except Exception:
            pass
        return

    finally:
        stop_event.set()
        print("Client disconnected from /api/live-transcription")

# ============================================================================
# SERVER START
# ============================================================================

if __name__ == "__main__":
    port = CONFIG["port"]
    host = CONFIG["host"]
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    print("\n" + "=" * 70)
    print(f"🚀 Flask Live Transcription Server (Backend API)")
    print("=" * 70)
    print(f"Server:   http://{host}:{port}")
    print(f"Debug:    {'ON' if debug else 'OFF'}")
    print("")
    print("📡 GET  /api/session")
    print("📡 WS   /api/live-transcription (auth required)")
    print("📡 GET  /api/metadata")
    print("=" * 70 + "\n")

    app.run(host=host, port=port, debug=debug)
