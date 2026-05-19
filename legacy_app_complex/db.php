<?php
// Legacy Database Connection
$db_host = 'localhost';
$db_user = 'root';
$db_pass = 'password123';
$db_name = 'shop_legacy';

$conn = mysqli_connect($db_host, $db_user, $db_pass, $db_name);

if (!$conn) {
    die("Connection failed: " . mysqli_connect_error());
}
?>
