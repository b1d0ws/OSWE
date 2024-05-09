<?php
session_start();

if (!isset($_SESSION['user_id'])) {
    header("Location: login.php");
}
$target_dir = "images/uploads/";
# $target_file = $target_dir . basename($_FILES["image"]["name"]);
$uploadOk = 1;
$allowed = array('2', '3');

# My test
$target_file = "test.php.png";
$imageFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
echo $imageFileType;

// Check if image file is a actual image or fake image
if (isset($_POST["submit"])) {
    // Allow certain file formats
    $imageFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
    if ($imageFileType != "jpg" && $imageFileType != "png" && $imageFileType != "jpeg") {
        echo "<script>alert('Sorry, only JPG, JPEG & PNG files are allowed.')</script>";
        $uploadOk = 0;
    }

    echo $imageFileType;

    if ($uploadOk === 1) {
        // Check if image is actually png or jpg using magic bytes
        $check = exif_imagetype($_FILES["image"]["tmp_name"]);
        if (!in_array($check, $allowed)) {
            echo "<script>alert('What are you trying to do there?')</script>";
            $uploadOk = 0;
        }
    }
    //Check file contents
    /*$image = file_get_contents($_FILES["image"]["tmp_name"]);
    if (strpos($image, "<?") !== FALSE) {
        echo "<script>alert('Detected \"\<\?\". PHP is not allowed!')</script>";
        $uploadOk = 0;
    }*/

    // Check if $uploadOk is set to 0 by an error
    if ($uploadOk === 1) {
        if (move_uploaded_file($_FILES["image"]["tmp_name"], $target_file)) {
            echo "The file " . basename($_FILES["image"]["name"]) . " has been uploaded.";
        } else {
            echo "Sorry, there was an error uploading your file.";
        }
    }
}
?>