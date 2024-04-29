import os
import platform

from datetime import datetime
net = input('Enter the network address: ')
net1 = net.split('.')
a = '.'

net2 = net1[0] + a + net1[1] + a + net1[2] + a
st1 = int(input("Enter the starting number: "))
en1 = int(input('Enter the last number: '))
en1 = en1 + 1
oper = platform.system

if (oper == "Windows"):
    ping1 = "ping -n 2 "
else:
    ping1 = "ping -c 2 "

t1 = datetime.now()
print("Scanning network %s from %d to %d" % (net, st1, en1 - 1))

for ip in range(st1,en1):
    addr = net2 + str(ip)
    command = ping1 + addr
    response = os.popen(command)

    print("Testing: %s" % (addr))

    for line in response.readlines():
        if ("ttl" in line):
            print(addr, "--> Live")
            break

t2 = datetime.now()
total = t2 - t1
print("Scanning completed in: ", total)

