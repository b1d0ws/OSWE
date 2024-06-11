$.ajax({
    url: 'http://unobtainium.htb:31337',
    type: 'get',
    
    success: function(data) {
        $("#output").html(JSON.stringify(data));
    }
});