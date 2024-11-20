# Flask Live Transcription Starter

Get started using Deepgram's Live Transcription with this Flask demo app.

## What is Deepgram?

[Deepgram](https://deepgram.com/) is a foundational AI company providing speech-to-text and language understanding capabilities to make data readable and actionable by human or machines.

## Sign-up to Deepgram

Before you start, it's essential to generate a Deepgram API key to use in this project. [Sign-up now for Deepgram and create an API key](https://console.deepgram.com/signup?jump=keys).

## Quickstart

### Manual

Follow these steps to get started with this starter application.

#### Clone the repository

Go to GitHub and [clone the repository](https://github.com/deepgram-starters/prerecorded-node-starter).

#### Install dependencies

Install the project dependencies.

```bash
pip install -r requirements.txt
```

#### Edit the config file

Copy the code from `sample.env` and create a new file called `.env`. Paste in the code and enter your API key you generated in the [Deepgram console](https://console.deepgram.com/).

```js
DEEPGRAM_API_KEY=%api_key%
```

#### Run the application

You need to run both app.py (port 8000) and app_socketio.py (port 5001). Once running, you can access the application in your browser at <http://127.0.0.1:8000>

```bash
python app.py
python app_socketio.py
```

## Testing

To contribute or modify pytest code, install the following dependencies:

```bash
pip install -r requirements-dev.txt
```

To run the tests, run the following command:

```bash
pytest -v -s
```

## Issue Reporting

If you have found a bug or if you have a feature request, please report them at this repository issues section. Please do not report security vulnerabilities on the public GitHub issue tracker. The [Security Policy](./SECURITY.md) details the procedure for contacting Deepgram.

## Getting Help

We love to hear from you so if you have questions, comments or find a bug in the project, let us know! You can either:

- [Open an issue in this repository](https://github.com/deepgram-starters/live-flask-starter/issues/new)
- [Join the Deepgram Github Discussions Community](https://github.com/orgs/deepgram/discussions)
- [Join the Deepgram Discord Community](https://discord.gg/xWRaCDBtW4)

## Author

[Deepgram](https://deepgram.com)

## License

This project is licensed under the MIT license. See the [LICENSE](./LICENSE) file for more info.
