<?php
require_once('db.php');
require_once('functions.php');
require_once('logger.php');

$error = '';
$success = '';

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = clean_input($_POST['username']);
    $email = clean_input($_POST['email']);
    $password = clean_input($_POST['password']);
    
    // Check if user exists
    $check_query = "SELECT id FROM users WHERE username = '$username' OR email = '$email'";
    $check_result = mysqli_query($conn, $check_query);
    
    if (mysqli_num_rows($check_result) > 0) {
        $error = "Username or Email already exists!";
        log_event("Failed registration attempt for username: $username", "WARN");
    } else {
        $hashed_password = md5($password);
        $date = date('Y-m-d H:i:s');
        
        $insert_query = "INSERT INTO users (username, password, email, role, created_at) VALUES ('$username', '$hashed_password', '$email', 'user', '$date')";
        
        if (mysqli_query($conn, $insert_query)) {
            $success = "Registration successful! You can now login.";
            log_event("New user registered: $username", "INFO");
        } else {
            $error = "Database error: " . mysqli_error($conn);
            log_event("DB Error during registration: " . mysqli_error($conn), "ERROR");
        }
    }
}

include('header.php');
?>
<h2>Register Account</h2>
<?php if($error != '') echo "<p class='error'>$error</p>"; ?>
<?php if($success != '') echo "<p class='success'>$success</p>"; ?>
<form method="POST" action="">
    <label>Username:</label><br>
    <input type="text" name="username" required><br><br>
    <label>Email:</label><br>
    <input type="email" name="email" required><br><br>
    <label>Password:</label><br>
    <input type="password" name="password" required><br><br>
    <input type="submit" value="Register">
</form>
<?php include('footer.php'); ?>
