import fire
import ptext
import pygame
import socket
from msg_decoder import decode_msg 

# set some globals
# SCREEN_WIDTH = 3000
# SCREEN_HEIGHT = 2000
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
# TODO - automaticaly detect wlan0 ip
#DISPLAY_HOST = "192.168.220.207"
DISPLAY_HOST = "127.0.0.1"
DISPLAY_PORT = 5000
PADDING = 50 
PADDING_TOP = 20
ONCE = True
FONT_SIZE = 64

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
    font = pygame.font.Font(FONT_FILE, 36)

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

        # render text to screen - use ptext for easy text wrapping
        if fill:
            screen.fill((255,255,255))
        if fill_top:
            screen.fill((255,255,255), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT / 2))
        if fill_bottom:
            screen.fill((255,255,255), (0, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        if text:
            ptext.draw(text, (PADDING, PADDING_TOP), color=(0,0,0), width=SCREEN_WIDTH-2*PADDING, fontname=FONT_FILE, lineheight=1, fontsize=FONT_SIZE, align="center")
        if text_bottom:
            ptext.draw(text_bottom, (PADDING, PADDING_TOP + (SCREEN_HEIGHT / 2)), color=(0,0,0), width=SCREEN_WIDTH-2*PADDING, fontname=FONT_FILE, lineheight=1, fontsize=FONT_SIZE, align="center")

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