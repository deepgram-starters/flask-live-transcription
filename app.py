import logging

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

app = Flask("app_http")


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    logging.info("Starting Flask server.")
    # Run flask app
    app.run(debug=True, port=8000)
