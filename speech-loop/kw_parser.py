import re
import time
import utils

TECKA_RE = r"\b(\w*(tečka))\b"
VYKRICNIK_RE = r"\b(\w*(vykřičník))\b"
OTAZNIK_RE = r"\b(\w*(otazník))\b"
CARKA_RE = r"\b(\w*(čárka))\b"

SMAZAT_RE = rf"\b(smazat)\b"
ZNOVU_RE = rf"\b(znovu)\b"
POKRACUJ_RE = rf"\b(pokračuj)\b"
VYCISTIT_RE = rf"\b(sorry|exit|quit|vyčistit)\b"
DIKY_RE = rf"\b(díky|Díky|jedeš)\b"

def replace_punct(text):
    text = re.sub(TECKA_RE, ".", text)
    text = re.sub(VYKRICNIK_RE, "!", text)
    text = re.sub(OTAZNIK_RE, "?", text)
    text = re.sub(CARKA_RE, ",", text)
    return text

def recognize_kws(text):
    s = time.time()

    delete = True if re.search(SMAZAT_RE, text, re.I) else False
    repeat = True if re.search(ZNOVU_RE, text, re.I) else False
    cont = True if re.search(POKRACUJ_RE, text, re.I) else False
    clear = True if re.search(VYCISTIT_RE, text, re.I) else False
    submit = True if re.search(DIKY_RE, text, re.I) else False

    kw_dict = {
        "delete": delete,
        "repeat": repeat,
        "continue": cont,
        "clear": clear,
        "submit": submit
    }

    utils.pmagenta(f"KW Recognition: {time.time() - s} seconds")
    return kw_dict