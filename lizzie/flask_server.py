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
TOKENS_LIMIT = 2048

# TODO add apikey to config
openai.api_key = os.getenv("OPENAI_API_KEY")

def log_request(input_text, engine, max_tokens, temperature):
    print("###### REQUEST:")
    print(input_text)
    print(engine)
    print(max_tokens)
    print(temperature)
    print()

def log_response(response):
    print("###### RESPONSE:")
    print(response)
    print()

def get_lizzie_response(input_text, engine=MODEL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):

    log_request(input_text, engine, max_tokens, temperature)

    resp = openai.Completion.create(engine=engine, prompt=input_text, max_tokens=max_tokens, temperature=temperature)
    
    log_response(resp)
    
    # Cut off unfinished sentence
    topResp = resp.choices[0]["text"]
    endIdx = max(topResp.rfind("."), topResp.rfind("?"), topResp.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return topResp[0: endIdx + 1]


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
    text = data["text"]
    engine = data["engine"] if data["engine"] else MODEL
    max_tokens = data["max_tokens"] if data["max_tokens"] else MAX_TOKENS
    temperature = data["temperature"] if data["temperature"] else TEMPERATURE

    # normalize temperature
    temperature = temperature / 100 if temperature > 1 else temperature

    respText = get_lizzie_response(text, engine, max_tokens, temperature)
    resp = {
        "text": respText,
        "sender": "Lizzie",
    }
    return json.dumps(resp)

# @APP.route('/engine', methods=['POST'])
# def set_engine():
#     engine = _get_json_from_request()["engine"]
#     print(engine)
#     global MODEL
#     MODEL = engine
#     return ""

# @APP.route('/temperature', methods=['POST'])
# def set_temperature():
#     temperature = _get_json_from_request()["temperature"]
#     print(temperature)
#     global TEMPERATURE
#     TEMPERATURE = temperature / 100
#     return ""

# @APP.route('/max_tokens', methods=['POST'])
# def set_max_tokens():
#     max_tokens = _get_json_from_request()["max_tokens"]
#     print(max_tokens)
#     global MAX_TOKENS
#     MAX_TOKENS = max_tokens
#     return ""