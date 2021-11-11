class DisplayManager:
    def __init__(self, app, display):
        self.app = app
        self.d = display

    
    def display(self):
        self.d.send(self.app.text_buffer, fill=False, fill_top=True)

    def display_intermediate(self, text):
        msg = (self.app.text_buffer + " " + text).strip()
        self.d.send(msg, fill=False, fill_top=True)

    def display_translation(self):
        self.d.send(
            text_bottom=self.app.trans_buffer,
            fill=False,
            fill_bottom=True
        )

    def clear_top(self):
        self.d.send(text=None, fill=False, fill_top=True)

    def clear_bottom(self):
        self.d.send(text=None, fill=False, fill_bottom=True)

    def clear(self):
        self.d.send(text=None, fill=True)