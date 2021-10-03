import socket

DISPLAY_HOST = "192.168.0.107"
DISPLAY_PORT = 5000

while True:
    # open connection
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
    conn.connect((DISPLAY_HOST, DISPLAY_PORT));
    
    # get input
    text = input()
    conn.send(text.encode());
    text = ""
        
    conn.close()