<?php
if(!isset($error_msg)){
					$uploaddir = UPLOAD_DIR.'tickets/';		
					if($_FILES['attachment']['error'] == 0){
						$ext = pathinfo($_FILES['attachment']['name'], PATHINFO_EXTENSION);
						$filename = md5($_FILES['attachment']['name'].time()).".".$ext;
						$fileuploaded[] = array('name' => $_FILES['attachment']['name'], 'enc' => $filename, 'size' => formatBytes($_FILES['attachment']['size']), 'filetype' => $_FILES['attachment']['type']);
						$uploadedfile = $uploaddir.$filename;
						if (!move_uploaded_file($_FILES['attachment']['tmp_name'], $uploadedfile)) {
							$show_step2 = true;
							$error_msg = $LANG['ERROR_UPLOADING_A_FILE'];
						}else{
							$fileverification = verifyAttachment($_FILES['attachment']);
							switch($fileverification['msg_code']){
								case '1':
								$show_step2 = true;
								$error_msg = $LANG['INVALID_FILE_EXTENSION'];
								break;
								case '2':
								$show_step2 = true;
								$error_msg = $LANG['FILE_NOT_ALLOWED'];
								break;
								case '3':
								$show_step2 = true;
								$error_msg = str_replace('%size%',$fileverification['msg_extra'],$LANG['FILE_IS_BIG']);
								break;
							}
						}
					}	
				}
?>