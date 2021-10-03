import pygame
import socket

# setup server
DISPLAY_HOST = "192.168.0.107"
DISPLAY_PORT = 5000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((DISPLAY_HOST, DISPLAY_PORT))
server_socket.listen(5)

pygame.init()
screen = pygame.display.set_mode((1024, 768), pygame.FULLSCREEN)
font = pygame.font.Font(pygame.font.get_default_font(), 36)
running =  True

while running:
    # get data from socket
    client_socket, address = server_socket.accept()
    text = client_socket.recv(200).decode()
    print("RX: {}".format(text))

    screen.fill((255,255,255))
    text_surface = font.render(text, True, (0, 0, 0))
    screen.blit(text_surface, dest=(512,0))
            
    pygame.display.flip()

pygame.quit()
