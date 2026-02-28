# flask-live-transcription

Flask demo app for Deepgram Live Transcription.

## Architecture

- **Backend:** Flask (Python) on port 8081
- **Frontend:** Vite + vanilla JS on port 8080 (git submodule: `live-transcription-html`)
- **API type:** WebSocket — `WS /api/live-transcription`
- **Deepgram API:** Live Speech-to-Text (`wss://api.deepgram.com/v1/listen`)
- **Auth:** JWT session tokens via `/api/session` (WebSocket auth uses `access_token.<jwt>` subprotocol)

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main backend — API endpoints and WebSocket proxy |
| `deepgram.toml` | Metadata, lifecycle commands, tags |
| `Makefile` | Standardized build/run targets |
| `sample.env` | Environment variable template |
| `frontend/main.js` | Frontend logic — UI controls, WebSocket connection, audio streaming |
| `frontend/index.html` | HTML structure and UI layout |
| `deploy/Dockerfile` | Production container (Caddy + backend) |
| `deploy/Caddyfile` | Reverse proxy, rate limiting, static serving |

## Quick Start

```bash
# Initialize (clone submodules + install deps)
make init

# Set up environment
test -f .env || cp sample.env .env  # then set DEEPGRAM_API_KEY

# Start both servers
make start
# Backend: http://localhost:8081
# Frontend: http://localhost:8080
```

## Start / Stop

**Start (recommended):**
```bash
make start
```

**Start separately:**
```bash
# Terminal 1 — Backend
./venv/bin/python app.py

# Terminal 2 — Frontend
cd frontend && corepack pnpm run dev -- --port 8080 --no-open
```

**Stop all:**
```bash
lsof -ti:8080,8081 | xargs kill -9 2>/dev/null
```

**Clean rebuild:**
```bash
rm -rf venv frontend/node_modules frontend/.vite
make init
```

## Dependencies

- **Backend:** `requirements.txt` — Uses Python venv for isolation. Always activate venv before running.
- **Frontend:** `frontend/package.json` — Vite dev server
- **Submodules:** `frontend/` (live-transcription-html), `contracts/` (starter-contracts)

Install: `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt`
Frontend: `cd frontend && corepack pnpm install`

## API Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/session` | GET | None | Issue JWT session token |
| `/api/metadata` | GET | None | Return app metadata (useCase, framework, language) |
| `/api/live-transcription` | WS | JWT | Streams microphone audio to Deepgram for real-time transcription. |

## Customization Guide

### Changing Default Parameters
The WebSocket connection URL passes parameters to Deepgram. Find where the Deepgram WebSocket URL is constructed in the backend and modify defaults:

| Parameter | Default | Options | Effect |
|-----------|---------|---------|--------|
| `model` | `nova-3` | `nova-3`, `nova-2`, `base` | STT model |
| `language` | `en` | Any BCP-47 code | Transcription language |
| `smart_format` | `true` | `true`/`false` | Smart formatting |
| `encoding` | `linear16` | `linear16`, `opus`, `flac` | Audio encoding |
| `sample_rate` | `16000` | `8000`, `16000`, `44100`, `48000` | Audio sample rate |
| `channels` | `1` | `1`, `2` | Mono or stereo |

### Adding More Deepgram Features via Query Params
These can be appended to the Deepgram WebSocket URL as query parameters:

| Feature | Parameter | Example | Effect |
|---------|-----------|---------|--------|
| Interim results | `interim_results` | `true` | Show partial transcripts while speaking |
| Endpointing | `endpointing` | `300` | Silence duration (ms) before finalization |
| Utterance end | `utterance_end_ms` | `1000` | Detect end of utterance |
| VAD events | `vad_events` | `true` | Voice activity detection events |
| Diarization | `diarize` | `true` | Speaker identification |
| Punctuation | `punctuate` | `true` | Auto-punctuation |
| Keywords | `keywords` | `deepgram:2` | Boost keyword with weight |
| No delay | `no_delay` | `true` | Minimize latency (may reduce accuracy) |

**Backend:** Append params to the Deepgram URL in the WebSocket proxy handler.

**Frontend:** The frontend sends these as query params when opening the WebSocket. To add a UI control for a new param, edit `frontend/main.js` — add an input/checkbox and include it in the `URLSearchParams` when connecting.

### Changing Audio Format
If changing from browser microphone (Linear16) to another source:
1. Update `encoding` and `sample_rate` params
2. The frontend captures audio via `AudioContext` at 16kHz and converts Float32 → Int16 PCM
3. If your audio source uses a different format, modify the frontend audio processing pipeline

## Frontend Changes

The frontend is a git submodule from `deepgram-starters/live-transcription-html`. To modify:

1. **Edit files in `frontend/`** — this is the working copy
2. **Test locally** — changes reflect immediately via Vite HMR
3. **Commit in the submodule:** `cd frontend && git add . && git commit -m "feat: description"`
4. **Push the frontend repo:** `cd frontend && git push origin main`
5. **Update the submodule ref:** `cd .. && git add frontend && git commit -m "chore(deps): update frontend submodule"`

**IMPORTANT:** Always edit `frontend/` inside THIS starter directory. The standalone `live-transcription-html/` directory at the monorepo root is a separate checkout.

### Adding a UI Control for a New Feature
1. Add the HTML element in `frontend/index.html` (input, checkbox, dropdown, etc.)
2. Read the value in `frontend/main.js` when making the API call or opening the WebSocket
3. Pass it as a query parameter in the WebSocket URL
4. Handle it in the backend `app.py` — read the param and pass it to the Deepgram API

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DEEPGRAM_API_KEY` | Yes | — | Deepgram API key |
| `PORT` | No | `8081` | Backend server port |
| `HOST` | No | `0.0.0.0` | Backend bind address |
| `SESSION_SECRET` | No | — | JWT signing secret (production) |

## Conventional Commits

All commits must follow conventional commits format. Never include `Co-Authored-By` lines for Claude.

```
feat(flask-live-transcription): add diarization support
fix(flask-live-transcription): resolve WebSocket close handling
refactor(flask-live-transcription): simplify session endpoint
chore(deps): update frontend submodule
```

## Testing

```bash
# Run conformance tests (requires app to be running)
make test

# Manual endpoint check
curl -sf http://localhost:8081/api/metadata | python3 -m json.tool
curl -sf http://localhost:8081/api/session | python3 -m json.tool
```
