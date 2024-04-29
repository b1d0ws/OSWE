#!/usr/bin/python3

# import httplib2
from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer

# Exercise 1 with urllib and beautifulSoup
url = urlopen("http://192.168.171.68:8080/crawling")

soup = BeautifulSoup(url.read(), features="html.parser")

# print(soup.prettify())

filter = soup.select('a')

webLinks = [webLink['href'] for webLink in filter]

print(webLinks)

for crawl in webLinks:

    secondURL = "http://192.168.171.68:8080" + crawl
    url = urlopen(secondURL)
    response = url.read().decode()

    if "OS" in response:
        print(response)

''' Exercise 1 with httplib2
http = httplib2.Http()
status, response = http.request("http://192.168.171.68:8080/crawling")

for link in BeautifulSoup(response, parse_only=SoupStrainer('a'), features="lxml"):
    
    if link.has_attr('href'):
        # print(link['href'])

        request = "http://192.168.171.68:8080/" + link['href']
        status, secondResponse = http.request(request)

        if "OS" in secondResponse.decode():
            print(secondResponse.decode())
'''

''' Exercise 2
url = urlopen("http://192.168.171.68:8080/table")

page = url.read()
soup = BeautifulSoup(page, features="html.parser")
find = soup.findAll('td')

for text in find:
    print(text.get_text(), end="")
'''
