<?php
// Legacy Header Include
ob_start(); // Legacy Hack to prevent "headers already sent" errors
if (session_status() == PHP_SESSION_NONE) {
    session_start();
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Legacy E-Commerce</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .nav { background: #eee; padding: 10px; margin-bottom: 20px; }
        .nav a { margin-right: 15px; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="dashboard.php">Home</a>
        <a href="cart.php">Cart</a>
        <?php if(isset($_SESSION['user_id'])): ?>
            <a href="profile.php">My Profile</a>
            <?php if(isset($_SESSION['role']) && $_SESSION['role'] === 'admin'): ?>
                <a href="admin_dashboard.php">Admin Panel</a>
            <?php endif; ?>
            <a href="logout.php">Logout (<?php echo htmlspecialchars($_SESSION['username']); ?>)</a>
        <?php else: ?>
            <a href="login.php">Login</a>
            <a href="register.php">Register</a>
        <?php endif; ?>
    </div>
    <div class="content">
