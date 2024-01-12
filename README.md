# Live Flask Starter

This sample demonstrates interacting with the Deepgram live streaming API using Flask, a micro web framework for Python.

## Sign-up to Deepgram

> Please leave this section unchanged, unless providing a UTM on the URL.

Before you start, it's essential to generate a Deepgram API key to use in this project. [Sign-up now for Deepgram](https://console.deepgram.com/signup).

## Quickstart

> Detail the manual steps to get started.

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

> Config file can be any appropriate file for the framework/language. For e.g.
> Node is using a config.json file, while Python is only use .env files

Copy the code from `sample.env` and create a new file called `.env`. Paste in the code and enter your API key you generated in the [Deepgram console](https://console.deepgram.com/).

```js
DEEPGRAM_API_KEY=%api_key%
```

#### Run the application

> to support the UI, it must always run on port 8080

Once running, you can access the application in your browser at <http://127.0.0.1:5000>

```bash
python app.py
```

## What is Deepgram?

Deepgram is an AI speech platform which specializes in (NLU) Natural Language Understanding features and Transcription. It can help get the following from your audio.

- [Speaker diarization](https://deepgram.com/product/speech-understanding/)
- [Language detection](https://deepgram.com/product/speech-understanding/)
- [Summarization](https://deepgram.com/product/speech-understanding/)
- [Topic detection](https://deepgram.com/product/speech-understanding/)
- [Language translation](https://deepgram.com/product/speech-understanding/)
- [Sentiment analysis](https://deepgram.com/product/speech-understanding/)
- [Entity detection](https://deepgram.com/product/speech-understanding/)
- [Transcription](https://deepgram.com/product/transcription/)
- [Redaction](https://deepgram.com/product/transcription/)

## Create a Free Deepgram Account

Before you start, it's essential to generate a Deepgram API key to use in our starter applications. [Sign-up now for Deepgram](https://console.deepgram.com/signup).

## Issue Reporting

If you have found a bug or if you have a feature request, please report them at this repository issues section. Please do not report security vulnerabilities on the public GitHub issue tracker. The [Security Policy](./SECURITY.md) details the procedure for contacting Deepgram.

## Author

[Deepgram](https://deepgram.com)

## License

This project is licensed under the MIT license. See the [LICENSE](./LICENSE) file for more info.
