import socket

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow

class DisplaySender:
    def __init__(self, host, port, font=None):
        self.host = host
        self.port = port
        self.font = font

    def _send(self, msg):
        sock = socket.socket()
        try:
            sock.connect((self.host, self.port))
            sock.send(msg.encode())
        except:
            pred(f"Cannot connect to {self.host}:{self.port}")
        finally:
            sock.close()

    def send(
        self,
        text="",
        text_bottom=None,
        fill=True,
        fill_top=None,
        fill_bottom=None,
        align=None,
        padding_left=None,
        padding_top=None,
        font=None,
        input_lang=None,
        output_lang=None,
        model=None,
        font_size=None):
        key_vals = []
        # Serialize all parameters
        if text:
            text = _sanitize_text(text)
            key_vals.append(_get_key_val("text", text))
        if text_bottom:
            text_bottom = _sanitize_text(text_bottom)
            key_vals.append(_get_key_val("text_bottom", text_bottom))
        if fill:
            key_vals.append(_get_key_val("fill", fill))
        if fill_top:
            key_vals.append(_get_key_val("fill_top", fill_top))
        if fill_bottom:
            key_vals.append(_get_key_val("fill_bottom", fill_bottom))
        if align:
            key_vals.append(_get_key_val("align", align))
        if padding_top:
            key_vals.append(_get_key_val("padding_top", padding_top))
        if padding_left:
            key_vals.append(_get_key_val("padding_left", padding_left))
        if font or self.font:
            f = font if font else self.font
            key_vals.append(_get_key_val("font", f))
        if input_lang:
            key_vals.append(_get_key_val("input_lang", input_lang))
        if output_lang:
            key_vals.append(_get_key_val("output_lang", output_lang))
        if model:
            key_vals.append(_get_key_val("model", model))
        if font_size:
            key_vals.append(_get_key_val("font_size", font_size))
        
        msg = _join_key_vals(key_vals)
        
        self._send(msg)
        return

def _get_key_val(key, val):
    return key + "=" + str(val)

def _join_key_vals(key_vals):
    return ":".join(key_vals)

def _sanitize_text(text):
    text = text.replace(":", "").replace("=", "")
    return text
