CHARS_PER_TOK = 4
CZK_PER_USD = 21.93
USD_PER_1000_TOKS = 0.06 # for Davinci

def text_to_crowns(text):
    """Apply GPT-3 pricing on the text and return the approximate price in Czech crowns."""
    tokens = len(text) / CHARS_PER_TOK
    return tokens * USD_PER_1000_TOKS / 1000 * CZK_PER_USD

def text_coda(text):
    return f'\nThis text cost {text_to_crowns(text)} crowns.'