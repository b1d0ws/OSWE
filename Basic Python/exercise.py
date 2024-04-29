#!/usr/bin/python3

import socket
import math

def checkPronic (x) :
 
    i = 0
    while ( i <= (int)(math.sqrt(x)) ) :
         
        # Checking Pronic Number 
        # by multiplying consecutive 
        # numbers
        if ( x == i * (i + 1)) :
            return True
        i = i + 1
 
    return False

target_IP = "192.168.171.68"

print('Starting scan on host: ', target_IP)

i = 4000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while (i <= 4999 ):
    if checkPronic(i):
        print("Pronic Port Found: ", i)
        
        conn = s.connect_ex((target_IP, i))
        if(conn == 0):
            print("Knocked!")
        
    i = i + 1

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)