$.ajax({url: "http://unobtainium.htb:31337",
        type: "HEAD",
        timeout:1000,
        statusCode: {
            200: function (response) {
                
            },
            400: function (response) {
                alert('Unable to reach unobtainium.htb');
            },
            0: function (response) {
                alert('Unable to reach unobtainium.htb');
            }              
        }
 });