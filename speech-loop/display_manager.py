import time
from utils import concat

class DisplayManager:
    def __init__(self, app, display, top_bottom_split=True, align="center", padding=None, display_translation_as_main=False):
        self.app = app
        self.d = display
        self.top_bottom_split = top_bottom_split
        self.align = align
        self.padding_top = padding[0]
        self.padding_left = padding[1]
        self.display_translation_as_main = display_translation_as_main

    def display(self):
        msg = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        fill = True if not self.top_bottom_split else False
        self.d.send(
            msg,
            fill=fill,
            fill_top=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )
        self.app.last_sent_time = time.time()

    def display_intermediate(self, text):
        buf = self.app.text_buffer_window if self.app.text_buffer_window is not None else self.app.text_buffer
        msg = (concat(buf, text)).strip()
        fill = True if not self.top_bottom_split else False
        self.d.send(
            msg,
            fill=fill,
            fill_top=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )
        self.app.last_sent_time = time.time()

    def display_translation(self):
        msg = self.app.trans_buffer_window if self.app.trans_buffer_window is not None else self.app.trans_buffer

        if self.display_translation_as_main:
            self.d.send(
                msg,
                fill=True,
                align=self.align,
                padding_top=self.padding_top,
                padding_left=self.padding_left,
            )
            return

        self.d.send(
            text_bottom=msg,
            fill=False,
            fill_bottom=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def display_action(self, msg, fill_color=None):
        self.d.send(
            text=msg,
            fill=True,
            fill_color=fill_color
        )
    
    def display_state(self, input_lang, output_lang, model):
        print("SENDING STATE")
        self.d.send(
            fill=False,
            fill_bottom=False,
            input_lang=input_lang,
            output_lang=output_lang,
            model=model
        )

    def clear_top(self):
        self.d.send(text=None, fill=False, fill_top=True)

    def clear_bottom(self):
        self.d.send(text=None, fill=False, fill_bottom=True)

    def clear(self):
        self.d.send(text=None, fill=True)
