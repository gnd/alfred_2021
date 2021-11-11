class DisplayManager:
    def __init__(self, app, display, top_bottom_split=True, align="center", padding=None, max_words=None):
        self.app = app
        self.d = display
        self.top_bottom_split = top_bottom_split
        self.align = align
        self.padding_top = padding[0]
        self.padding_left = padding[1]
        self.max_words = max_words

    
    def display(self):
        msg = self.app.text_buffer if self.max_words is None else self.chop_max_words(self.app.text_buffer)

        fill = True if not self.top_bottom_split else False
        self.d.send(
            msg,
            fill=fill,
            fill_top=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def display_intermediate(self, text):
        msg = (self.app.text_buffer + " " + text).strip()

        # Chop off only tail to show on display.
        msg = msg if self.max_words is None else self.chop_max_words(msg)

        fill = True if not self.top_bottom_split else False
        self.d.send(
            msg,
            fill=fill,
            fill_top=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def display_translation(self):
        t = self.app.trans_buffer if self.max_words is None else self.chop_max_words(self.app.trans_buffer)

        self.d.send(
            text_bottom=t,
            fill=False,
            fill_bottom=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def clear_top(self):
        self.d.send(text=None, fill=False, fill_top=True)

    def clear_bottom(self):
        self.d.send(text=None, fill=False, fill_bottom=True)

    def clear(self):
        self.d.send(text=None, fill=True)

    def chop_max_words(self, text):
        if self.max_words is not None:
            words = text.split(" ")
            if len(words) > self.max_words:
                return " ".join(words[-self.max_words:])
            else:
                return text