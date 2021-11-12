import os
import re
import six
from termcolor import cprint, colored

from kw_parser import replace_punct

CHARS_PER_TOK = 4
CZK_PER_USD = 21.93
USD_PER_1000_TOKS = 0.06 # for Davinci

# Logging functions

pblue = lambda text: cprint(text, "blue")
pred = lambda text: cprint(text, "red")
pgreen = lambda text: cprint(text, "green")
pyellow = lambda text: cprint(text, "yellow")
pcyan = lambda text: cprint(text, "cyan")
pmagenta = lambda text: cprint(text, "magenta")

cblue = lambda text: colored(text, "blue")
cred = lambda text: colored(text, "red")
cgreen = lambda text: colored(text, "green")
cyellow = lambda text: colored(text, "yellow")
ccyan = lambda text: colored(text, "cyan")
cmagenta = lambda text: colored(text, "magenta")

def prainbow(*args):
    col_to_func = {
        "b": cblue,
        "r": cred,
        "g": cgreen,
        "y": cyellow,
        "c": ccyan,
        "m": cmagenta,
        "w": lambda x: x
    }
    output = []
    for x in args:
        if col_to_func[x[1]]:
            output.append(col_to_func[x[1]](x[0]))
        else:
            print("Unknown color", x[1])

    print(" ".join(output))

def beep(seconds=1):
    os.system('play -nq -t alsa synth {} sine {}'.format(seconds, 440))

def elapsed_time(start, end):
    return f'{"{:.3f}".format(end - start)} seconds'

def text_to_crowns(text):
    """Apply GPT-3 pricing on the text and return the approximate price in Czech crowns."""
    tokens = len(text) / CHARS_PER_TOK
    return tokens * USD_PER_1000_TOKS / 1000 * CZK_PER_USD

def text_coda(text):
    return f'\nThis text cost {text_to_crowns(text)} crowns.'

def recognize_stop_word(text):
    if re.search(r"\b(quit|exit|sorry)\b", text, re.I):
        pmagenta(",.-~*´¨¯¨`*·~-.¸-( Stopword Detected )-,.-~*´¨¯¨`*·~-.¸")
        return True
    else:
        return False

def cut_to_sentence_end(text):
    """Cuts off unfinished sentence."""

    endIdx = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return text[0: endIdx + 1]

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    text = text.lstrip(". ")               # remove leftover dots and spaces from the beggining
    text = text.replace("&quot;","")       # remove "&quot;"
    text = text.strip()
    return text

def sanitize_translation(text):
    t = text.replace("&#39;", "'")
    t = text.replace("“", "")
    t = text.replace("”", "")
    t = text.replace("’", "")
    t = text.replace("‘", "")
    t = text.replace("\"", "")
    if len(t) > 2:
        t = t[0].upper() + t[1:] # Capitalize; `capitalize` sucks
    elif len(t) == 1:
        t = t.upper()
    return t

def concat(a, b):
    a = a.strip()
    b = replace_punct(b)
    b = b.strip()
    if len(b) > 0:
        if b[0] == "." or b[0] == "?" or b[0] == "!" or b[0] == ",":
            return a + b
        else:
            return a + " " + b
    return a

SPEECH_CODE_TO_LANG_CODE = {
    "cs-CZ": "cs",
    "en-US": "en",
    "fr-FR": "fr",
    "de-DE": "de",
    "ru-RU": "ru",
    "cmn-CN": "zh-CN"
}

class SpeechCode:
    def __init__(self):
        self.CZECH = "cs-CZ"
        self.ENGLISH = "en-US"
        self.FRENCH = "fr-FR"
        self.GERMAN = "de-DE"
        self.RUSSIAN = "ru-RU"
        self.CHINESE = "cmn-CN"

class LangCode:
    def __init__(self):
        self.CZECH = "cs"
        self.ENGLISH = "en"
        self.FRENCH = "fr"
        self.GERMAN = "de"
        self.RUSSIAN = "ru"
        self.CHINESE = "zh-CN"

def getLangCode(speech_code):
    return SPEECH_CODE_TO_LANG_CODE.get(speech_code)

def delete_word(text):
    """Deletes the last word from `text`."""
    text = text.split()
    if len(text) > 0:
        return " ".join(text[:-1])
    else:
        return text