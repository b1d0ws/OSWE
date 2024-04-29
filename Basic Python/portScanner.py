#!/usr/bin/python3

import socket
import time

startTime = time.time()

target = input('Enter the host to be scanned: ')
# target_IP = socket.gethostbyname(target)

target_IP = "192.168.171.68"

print('Starting scan on host: ', target_IP)

# Range of ports
for i in range(4000, 4999):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    conn = s.connect_ex((target_IP, i))

    if(conn == 0):
        print('Port %d: OPEN' % (i))
    s.close()

print('Time taken:', time.time() - startTime)