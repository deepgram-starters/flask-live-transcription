# Flask Live Transcription Starter

Live Speech-to-Text demo using Deepgram's API with Python Flask backend and web frontend.

## Prerequisites

- [Deepgram API Key](https://console.deepgram.com/signup?jump=keys) (sign up for free)
- Python 3.9+
- Node.js 14+ and pnpm (for frontend build)

## Quick Start

### 1. Install dependencies

**Backend (Python):**

```bash
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm run build
cd ..
```

### 2. Set your API key

Create a `.env` file:

```bash
DEEPGRAM_API_KEY=your_api_key_here
```

### 3. Run the app

**Production mode**:

```bash
python app.py
```

Open [http://localhost:3000](http://localhost:3000)

**Development mode with frontend HMR** (optional, for frontend development):

```bash
# Terminal 1: Backend
python app.py

# Terminal 2: Frontend dev server with instant reload
cd frontend && pnpm run dev
```

Open [http://localhost:5173](http://localhost:5173)


## Features

This application:

- Accepts a live audio stream URL via WebSocket connection
- Fetches the audio stream from the provided URL
- Sends binary audio data to Deepgram's live Speech-to-Text API
- Returns real-time transcription results to the client

## How It Works

- **Backend** (`app.py`): Flask server implementing the `/stt/transcribe` endpoint per the STT API contract
- **Frontend** (`frontend/`): Vite-powered web UI built with Deepgram design system
- **API**: Integrates with [Deepgram's Speech-to-Text API](https://developers.deepgram.com/)

The frontend is built with Vite and served as static files from `frontend/dist/`. This ensures a consistent UI across all Deepgram starter apps regardless of backend language.

## Getting Help

We love to hear from you so if you have questions, comments or find a bug in the project, let us know! You can either:

- [Open an issue in this repository](https://github.com/deepgram-starters/flask-live-transcription/issues/new)
- [Join the Deepgram Github Discussions Community](https://github.com/orgs/deepgram/discussions)
- [Join the Deepgram Discord Community](https://discord.gg/xWRaCDBtW4)

## Contributing

See our [Contributing Guidelines](./CONTRIBUTING.md) to learn about contributing to this project.

## Code of Conduct

This project follows the Deepgram [Code of Conduct](./CODE_OF_CONDUCT.md)

## Security

For security policy and procedures, see our [Security Policy](./SECURITY.md)



## License

MIT See [LICENSE](./LICENSE)
