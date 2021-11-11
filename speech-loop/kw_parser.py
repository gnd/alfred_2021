import re
import time

TECKA_RE = r"\b(\w*(tečka|Tečka))\b"
VYKRICNIK_RE = r"\b(\w*(vykřičník|Vykřičník))\b"
OTAZNIK_RE = r"\b(\w*(otazník|Otazník))\b"
CARKA_RE = r"\b(\w*(čárka|Čárka))\b"

def replace_punct(text):
    text = re.sub(TECKA_RE, ".", text)
    text = re.sub(VYKRICNIK_RE, "!", text)
    text = re.sub(OTAZNIK_RE, "?", text)
    text = re.sub(CARKA_RE, ",", text)
    return text
