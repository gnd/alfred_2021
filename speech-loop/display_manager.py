class DisplayManager:
    def __init__(self, app, display, top_bottom_split=True, align="center", padding=(20, 50)):
        self.app = app
        self.d = display
        self.top_bottom_split = top_bottom_split
        self.align = align
        self.padding_top = padding[0]
        self.padding_left = padding[1]

    
    def display(self):
        fill = True if not self.top_bottom_split else False
        self.d.send(
            self.app.text_buffer,
            fill=fill,
            fill_top=True,
            align=self.align,
            padding_top=self.padding_top,
            padding_left=self.padding_left,
        )

    def display_intermediate(self, text):
        msg = (self.app.text_buffer + " " + text).strip()
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
        self.d.send(
            text_bottom=self.app.trans_buffer,
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