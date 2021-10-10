import os
import json

import openai
from flask import Flask, render_template, request, send_file


# Create the Flask server.
APP = Flask(__name__, static_folder="frontend/build/", template_folder="frontend/build", static_url_path="")

# Initialize OpenAI
MAX_TOKENS = 200
TEMPERATURE = 0.9
MODEL = "davinci"

# TODO add apikey to config
openai.api_key = os.getenv("OPENAI_API_KEY")

def logResponse(response):
    print(response)
    print()

def getLizzieResponse(inputText):
    max_tokens = MAX_TOKENS - len(inputText)
    resp = openai.Completion.create(engine=MODEL, prompt=inputText, max_tokens=max_tokens, temperature=TEMPERATURE)
    logResponse(resp)
    topResp = resp.choices[0]["text"]
    endIdx = max(topResp.rfind("."), topResp.rfind("?"), topResp.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    return topResp[0: endIdx + 1]


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

@APP.route('/engine', methods=['POST'])
def set_engine():
    engine = _get_json_from_request()["engine"]
    print(engine)
    global MODEL
    MODEL = engine
    return ""

@APP.route('/temperature', methods=['POST'])
def set_temperature():
    temperature = _get_json_from_request()["temperature"]
    print(temperature)
    global TEMPERATURE
    TEMPERATURE = temperature / 100
    return ""

@APP.route('/max_tokens', methods=['POST'])
def set_max_tokens():
    max_tokens = _get_json_from_request()["max_tokens"]
    print(max_tokens)
    global MAX_TOKENS
    MAX_TOKENS = max_tokens
    return ""