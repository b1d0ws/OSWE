#!/usr/bin/python3

import socket

host = socket.gethostname()
port = 8080

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((host, port))

print(client.recv(1024).decode())

client.close()