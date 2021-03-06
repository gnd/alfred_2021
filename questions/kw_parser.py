import re
import time
import utils

TECKA_RE = r"\b(\w*(tečka))\b"
VYKRICNIK_RE = r"\b(\w*(vykřičník))\b"
OTAZNIK_RE = r"\b(\w*(otazník))\b"
CARKA_RE = r"\b(\w*(čárka))\b"

SMAZAT_RE = rf"\b(smazat|delete)\b"
ZNOVU_RE = rf"\b(znovu|repeat)\b"
POKRACUJ_RE = rf"\b(pokračuj|continue)\b"
VYCISTIT_RE = rf"\b(sorry|exit|quit|vyčistit|clear)\b"
DIKY_RE = rf"\b(díky|Díky|jedeš|I'm out|peace out)\b"

INSTRUCT_RE = rf"\b(model instruct|engine instruct|model instrukce|motor instrukce)\b"
NORMAL_RE = rf"\b(model normal|engine normal|model normální|motor normální)\b"

IN_CS_RE = rf"\b(input Czech|input check|input chess|input chair|input bohemian|bohemian in|Czech in)\b"
IN_EN_RE = rf"\b(vstup anglicky)\b"

OUT_CS_RE = rf"\b(output Czech|output check|output chess|output chair|výstup česky|output bohemian|bohemian out)\b"
OUT_EN_RE = rf"\b(output English|výstup anglicky)\b"

ZOBRAZ_RE = rf"\b(zobraz|ukaž|show)\b"

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

    instruct = True if re.search(INSTRUCT_RE, text, re.I) else False
    normal = True if re.search(NORMAL_RE, text, re.I) else False

    in_czech = True if re.search(IN_CS_RE, text, re.I) else False
    in_english = True if re.search(IN_EN_RE, text, re.I) else False

    out_czech = True if re.search(OUT_CS_RE, text, re.I) else False
    out_english = True if re.search(OUT_EN_RE, text, re.I) else False

    show = True if re.search(ZOBRAZ_RE, text, re.I) else False

    kw_dict = {
        "delete": delete,
        "repeat": repeat,
        "continue": cont,
        "clear": clear,
        "submit": submit,
        "instruct": instruct,
        "normal": normal,
        "in_czech": in_czech,
        "in_english": in_english,
        "out_czech": out_czech,
        "out_english": out_english,
        "show": show
    }

    utils.pmagenta(f"KW Recognition: {time.time() - s} seconds")
    return kw_dict