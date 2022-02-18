import fire
import ptext
import pygame
import socket
from msg_decoder import decode_msg 

# set some globals
# SCREEN_WIDTH = 3000
# SCREEN_HEIGHT = 2000
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000
# TODO - automaticaly detect wlan0 ip
#DISPLAY_HOST = "192.168.217.207"
DISPLAY_HOST = "127.0.0.1"
DISPLAY_PORT = 5000
PADDING_LEFT = 80 
PADDING_TOP = 100
ONCE = True
FONT_SIZE = 72
STATE_FONT_SIZE = 36

FONT_FILE = "./fonts/Roboto-MediumItalic.ttf"

def main(port=DISPLAY_PORT, host=DISPLAY_HOST):
    # setup listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    # init pygame
    pygame.init()
    #screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # font = pygame.font.Font(pygame.font.get_default_font(), 36)
    font = pygame.font.Font(FONT_FILE, STATE_FONT_SIZE)

    running =  True
    while running:
        # blank screen on start
        global ONCE
        if ONCE:
            screen.fill((255,255,255))
            pygame.display.flip()
            ONCE = False
    
        # get data from socket - blocking
        # TODO - do a threaded non-blocking version
        client_socket, address = server_socket.accept()
        
        msg = client_socket.recv(1024).decode()
        
        msg_dict = decode_msg(msg)
        print("RX: {}".format(msg_dict))

        text = msg_dict.get("text")
        text_bottom = msg_dict.get("text_bottom")
        fill = msg_dict.get("fill")
        fill_top = msg_dict.get("fill_top")
        fill_bottom = msg_dict.get("fill_bottom")
        font_fname = msg_dict.get("font") if msg_dict.get("font") else pygame.font.get_default_font()
        align = msg_dict.get("align")
        padding_top = int(msg_dict.get("padding_top")) if msg_dict.get("padding_top") else PADDING_TOP
        padding_left = int(msg_dict.get("padding_left")) if msg_dict.get("padding_left") else PADDING_LEFT
        fill_color = msg_dict.get("fill_color")
        input_lang = msg_dict.get("input_lang")
        output_lang = msg_dict.get("output_lang")
        model = msg_dict.get("model")
        font_size = msg_dict.get("font_size")

        font_size = int(font_size) if font_size else FONT_SIZE

        fc = (255,255,255)
        if fill_color:
            fc = [int(c) for c in fill_color.split("!")]
            fc = (fc[0], fc[1], fc[2])

        # render text to screen - use ptext for easy text wrapping
        if fill:
            screen.fill(fc, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        if fill_top:
            screen.fill(fc, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT / 2))
        if fill_bottom:
            screen.fill(fc, (0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        if text:
            ptext.draw(
                text,
                (padding_left, padding_top),
                color=(0,0,0),
                width=SCREEN_WIDTH-2*padding_left,
                fontname=font_fname,
                lineheight=1,
                fontsize=font_size,
                align=align
            )

        if text_bottom:
            ptext.draw(
                text_bottom,
                (padding_left,
                padding_top + (SCREEN_HEIGHT / 2)),
                color=(0,0,0),
                width=SCREEN_WIDTH-2*padding_left,
                fontname=font_fname,
                lineheight=1,
                fontsize=font_size,
                align=align
            )
            
        if input_lang:
            ptext.draw(
                "In: {} Out: {} Model: {}".format(input_lang.strip(), output_lang.strip(), model.strip()),
                (10, SCREEN_HEIGHT - 40),
                color=(0,0,0),
                width=SCREEN_WIDTH,
                fontname=font_fname,
                lineheight=1,
                fontsize=STATE_FONT_SIZE,
                align=align
            )

        # handle some events
        # This will work properly once non-blocking socket is done
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("Esc key press detected")
                    running = False
   
        pygame.display.flip()

    server_socket.close()
    pygame.quit()


if __name__ == "__main__":
    fire.Fire(main)
