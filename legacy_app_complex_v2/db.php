<?php
// Procedural Database connection configuration
$host = "localhost";
$db_user = "root";
$db_pass = "";
$db_name = "crm_enterprise_db";

$conn = mysqli_connect($host, $db_user, $db_pass, $db_name);

if (!$conn) {
    die("CRITICAL ERROR: CRM Database Connection failed: " . mysqli_connect_error());
}

// Enable UTF-8 encoding
mysqli_set_charset($conn, "utf8mb4");
?>
