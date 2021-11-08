import time
import socket

DISPLAY_HOST = "127.0.0.1"
DISPLAY_PORT = 5000

def send_msg(msg):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
    conn.connect((DISPLAY_HOST, DISPLAY_PORT));
    conn.send(msg.encode());
    conn.close()

    time.sleep(0.125)

def a1():
    text = "(>_>)"
    send_msg(text)
    text = "(<_<)"
    send_msg(text)
    text = "(x_x)"
    send_msg(text)
    text = " (x_x)"
    send_msg(text)
    text = "  (x_x)"
    send_msg(text)
    text = "   (x_x)"
    send_msg(text)
    text = "    (x_x)"
    send_msg(text)
    text = "   (x_x)"
    send_msg(text)
    text = "  (x_x)"
    send_msg(text)
    text = " (x_x)"
    send_msg(text)
    text = "(x_x)"
    send_msg(text)

def shift_text(text):
    return text[-1] + text[0:-1]

def pad_to_len(text, tot_len):
    return text + (" " * (tot_len - len(text)))

def appear_word(text):
    for x in range(len(text)):
        y = len(text) - x
        send_msg(text[y:])

def shift_text_alt(text):
    return " " + text[0:-1]
    
def showtime_text(text, max_length):
    appear_word(text)
    text = pad_to_len(text, max_length)
    for x in range(max_length):
        send_msg(text)
        # text = shift_text(text)
        text = shift_text_alt(text)

def a3():
    # text = "OK CARBON"
    # length = 51
    # text = pad_to_len(text, length)
    LENGHT = 51
    while True:
        showtime_text("OK CARBON", LENGHT)
        showtime_text("THIS IS", LENGHT)
        showtime_text("AN IMPORTANT MESSAGE", LENGHT)
        showtime_text("FROM", LENGHT)
        showtime_text("ARTIFICIAL", LENGHT)
        showtime_text("INTELLIGENCE", LENGHT)
        showtime_text("GO VEGAN", LENGHT)
        showtime_text("DRINK WATER", LENGHT)
        showtime_text("3.7 LITERS", LENGHT)
        showtime_text("PER DAY", LENGHT)
        showtime_text("FOR MEN", LENGHT)
        showtime_text("2.7 LITERS", LENGHT)
        showtime_text("FOR WOMEN", LENGHT)
        showtime_text("THAT IS", LENGHT)
        showtime_text("11.5 CUPS", LENGHT)
        showtime_text("FOR WOMEN", LENGHT)
        showtime_text("AND", LENGHT)
        showtime_text("15.5 CUPS", LENGHT)
        showtime_text("FOR MEN", LENGHT)
        showtime_text("OK?", LENGHT)

def a4():
    LENGTH = 51
    while True:
        showtime_text("TUTORIAL", LENGTH)


def instructions():
    instructs = [
        "     ,.-~*´¨¯¨`*·~-.¸-_   repeat carbon   _-,.-~*´¨¯¨`*·~-.¸",
        "",
        "Anglicky                           Cesky",
        "",
        "engine normal/instruct   motor normální/instrukce",
        "temperature 0-100           teplota 0-100",
        "input Czech                      vstup anglicky",
        "output Czech/English     výstup česky/anglicky",
        "I'm out/peace out              díky/jedeš",
        "exit/quit/sorry                   exit/quit/sorry",
        "repeat                                 znovu",
        "delete                                 smazat",
        "backspace                          backspace",
        "continue                             pokračuj",
    ]
    send_msg("\n".join(instructs))
        

while True:
    # a1()
    # a3()
    instructions()
