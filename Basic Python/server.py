#!/usr/bin/python3

import socket

host = "192.168.45.168"
port = 8080

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind port to start listening
server.bind((host, port))

# Set the maximum connections that kepts waiting for the server
server.listen(4)
print('Server is listening for incoming connections')

while True:
    conn,addr = server.accept()
    print("Connection Received from %s" % str(addr))
    msg = 'Connection Establised' + "\r\n"
    conn.send(msg.encode('ascii'))
    conn.close()
