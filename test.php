<?php
// Legacy PHP script for testing WebLegacy AI migration
include('db_config.php');

$userId = $_GET['id'];

if (empty($userId)) {
    die("Error: No user ID provided.");
}

// Typical insecure legacy SQL query
$query = "SELECT id, username, email, created_at FROM users WHERE id = " . $userId;
$result = mysqli_query($conn, $query);

if (!$result) {
    die("Database query failed: " . mysqli_error($conn));
}

$user = mysqli_fetch_assoc($result);

if ($user) {
    echo "<h1>User Profile</h1>";
    echo "<p>Username: " . htmlspecialchars($user['username']) . "</p>";
    echo "<p>Email: " . $user['email'] . "</p>";
    echo "<p>Member since: " . $user['created_at'] . "</p>";
} else {
    echo "User not found.";
}

mysqli_close($conn);
?>
