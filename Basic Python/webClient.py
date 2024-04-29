#!/usr/bin/python3

import requests


url = "http://192.168.171.68:8080/{}.html"

for i in range(1, 50):

    actualURL = url.format(i)

    response = requests.get(actualURL)
    print(response.text.strip(), end="")

