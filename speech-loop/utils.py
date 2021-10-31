import re
import six

CHARS_PER_TOK = 4
CZK_PER_USD = 21.93
USD_PER_1000_TOKS = 0.06 # for Davinci

def text_to_crowns(text):
    """Apply GPT-3 pricing on the text and return the approximate price in Czech crowns."""
    tokens = len(text) / CHARS_PER_TOK
    return tokens * USD_PER_1000_TOKS / 1000 * CZK_PER_USD

def text_coda(text):
    return f'\nThis text cost {text_to_crowns(text)} crowns.'


def recognize_stop_word(text):
    if re.search(r"\b(quit|exit)\b", text, re.I):
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
    return text
