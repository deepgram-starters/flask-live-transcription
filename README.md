# Flask Live Transcription Starter

Live speech-to-text transcription demo using Deepgram's API with Python Flask backend and web frontend.

## Prerequisites

- [Deepgram API Key](https://console.deepgram.com/signup?jump=keys) (sign up for free)
- Python 3.9+
- pnpm 10+ (for frontend)

**Note:** This project uses git submodules for the frontend.

## Quick Start

1. **Clone the repository**

Clone the repository with submodules (the frontend is a shared submodule):

```bash
git clone --recurse-submodules https://github.com/deepgram-starters/flask-live-transcription.git
cd flask-live-transcription
```

2. **Install dependencies**

```bash
# Option 1: Use Makefile (recommended)
make init

# Option 2: Manual install
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd frontend && pnpm install && cd ..
```

3. **Set your API key**

Create a `.env` file:

```bash
DEEPGRAM_API_KEY=your_api_key_here
```

4. **Run the app**

**Development mode** (with hot reload):

```bash
make dev
```

**Production mode** (build and serve):

```bash
make build
make start
```

### 🌐 Open the App
[http://localhost:8080](http://localhost:8080)

## Features

- Real-time speech-to-text transcription
- Live audio streaming with visual feedback
- Multiple model options
- Connection statistics

## Architecture

### Backend
Flask server with WebSocket support (using Flask-Sock):
- WebSocket endpoint: `/live-stt/stream`
- Accepts binary audio streams from frontend
- Proxies audio to Deepgram's live API
- Streams back real-time transcription results
- Serves built frontend from `frontend/dist/`

### Frontend
- Real-time microphone capture and transcription
- Pure vanilla JavaScript (no frameworks)
- Deepgram Design System for styling

## How It Works

1. **Client connects** to `/live-stt/stream` WebSocket endpoint with optional model and language parameters
2. **Flask-Sock** handles the WebSocket connection using native WebSocket support
3. **Server establishes** a connection to Deepgram's live API
4. **Audio flows** from client → Flask → Deepgram
5. **Transcripts stream** back from Deepgram → Flask → client in real-time
6. **Results formatted** according to the live-stt API contract with type, transcript, confidence, and metadata

## Makefile Commands

This project includes a Makefile for framework-agnostic operations:

```bash
make help              # Show all available commands
make init              # Initialize submodules and install dependencies
make dev               # Start development servers
make build             # Build frontend for production
make start             # Start production server
make update            # Update submodules to latest
make clean             # Remove venv, node_modules and build artifacts
make status            # Show git and submodule status
```

Use `make` commands for a consistent experience regardless of language.

## Getting Help

- [Open an issue](https://github.com/deepgram-starters/flask-live-transcription/issues/new)
- [Join our Discord](https://discord.gg/xWRaCDBtW4)
- [Deepgram Documentation](https://developers.deepgram.com/)

## Security

This project implements security best practices including:
- Dependency pinning to exact versions
- Automated vulnerability scanning with Snyk
- Environment variable management

See [SECURITY.md](./.github/SECURITY.md) for complete security documentation and reporting procedures.

## Contributing

Contributions are welcome! Please review:
- [Contributing Guidelines](./.github/CONTRIBUTING.md)
- [Code of Conduct](./.github/CODE_OF_CONDUCT.md)
- [Security Policy](./.github/SECURITY.md)

## License

MIT - See [LICENSE](./LICENSE)
