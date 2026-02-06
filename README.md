# Flask Live Transcription

Get started using Deepgram's Live Transcription with this Flask demo app

<!-- [**Live Demo \u2192**](#) -->

## Quick Start

Click the button below to fork the repo:

[![Fork on GitHub](https://img.shields.io/badge/Fork_on_GitHub-blue?logo=github)](https://github.com/deepgram-starters/flask-live-transcription/fork)

## Local Development

<!--
### CLI

```bash
dg check
dg install
dg start
```
-->

### Makefile (Recommended)

```bash
make init
cp sample.env .env  # Add your DEEPGRAM_API_KEY
make start
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

### Python & pnpm

```bash
git clone --recurse-submodules https://github.com/deepgram-starters/flask-live-transcription.git
cd flask-live-transcription
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cd frontend && corepack pnpm install && cd ..
cp sample.env .env  # Add your DEEPGRAM_API_KEY
```

Start both servers in separate terminals:

```bash
# Terminal 1 - Backend (port 8081)
./venv/bin/python app.py

# Terminal 2 - Frontend (port 8080)
cd frontend && corepack pnpm run dev -- --port 8080 --no-open
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

## License

MIT - See [LICENSE](./LICENSE)
