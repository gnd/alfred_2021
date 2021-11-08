import fire
import pygame
import socket
import ptext

# set some globals
SCREEN_WIDTH = 1900
SCREEN_HEIGHT = 1000
# TODO - automaticaly detect wlan0 ip
#DISPLAY_HOST = "192.168.220.207"
DISPLAY_HOST = "127.0.0.1"
DISPLAY_PORT = 5000
PADDING = 50 
PADDING_TOP = 50 
ONCE = True
FONT_SIZE = 90

def main(port=DISPLAY_PORT, host=DISPLAY_HOST):
    # setup listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    # init pygame
    pygame.init()
    #screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.Font(pygame.font.get_default_font(), 36)

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
        text = client_socket.recv(1024).decode()
        print("RX: {}".format(text))

        # render text to screen - use ptext for easy text wrapping
        screen.fill((255,255,255))
        ptext.draw(text, (PADDING, PADDING_TOP), color=(0,0,0), width=SCREEN_WIDTH-2*PADDING, lineheight=1, fontsize=FONT_SIZE)
            
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