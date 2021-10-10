import os
import json

import openai
from flask import Flask, render_template, request, send_file


# Create the Flask server.
APP = Flask(__name__, static_folder="frontend/build/", template_folder="frontend/build", static_url_path="")

# Initialize OpenAI
MAX_TOKENS = 2048
TEMPERATURE = 0.9
openai.api_key = os.getenv("OPENAI_API_KEY")

def logResponse(response):
    print(response)
    print()

def getLizzieResponse(inputText):
    max_tokens = MAX_TOKENS - len(inputText)
    resp = openai.Completion.create(engine="davinci", prompt=inputText, max_tokens=max_tokens, temperature=TEMPERATURE)
    logResponse(resp)
    return resp.choices[0]["text"]


# APP.config['gpt-3'] = STATE

def _get_json_from_request():
    return request.get_json(force=True)

def start_server(port, public):
    """Start the Flask server.
    
    This function blocks until the web server stops.
    """

    # APP.debug = False
    APP.debug = True
    host = '0.0.0.0' if public else '127.0.0.1'
    
    # APP.run() launches Flask's built-in HTTP server.
    # The function call is blocking - the server waits
    # for user requests and handles them until terminated
    # or until an error occurs.
    APP.run(host=host, port=port)

@APP.route('/', methods=['GET'])
def init():
    """Handle requests for the root page.
    Returns:
        A HTML document in a string.
    """

    return render_template('index.html')

@APP.route('/lizzie', methods=['POST'])
def answer():
    data = _get_json_from_request()
    
    print(data)

    respText = getLizzieResponse(data["text"])
    resp = {
        "text": respText,
        "sender": "Lizzie",
    }
    return json.dumps(resp)