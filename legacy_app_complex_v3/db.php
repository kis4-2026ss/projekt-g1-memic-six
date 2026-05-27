<?php
// Database connection for Enterprise Warehouse Management System
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "warehouse_erp_v3";

// Create connection
$conn = mysqli_connect($servername, $username, $password, $dbname);

// Check connection
if (!$conn) {
    die("Database connection failed: " . mysqli_connect_error());
}
?>
