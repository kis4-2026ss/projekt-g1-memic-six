<?php
// Support application/json POST bodies for automated validation testing
if ($_SERVER['REQUEST_METHOD'] === 'POST' && strpos($_SERVER['HTTP_CONTENT_TYPE'] ?? $_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== false) {
    $raw_input = file_get_contents('php://input');
    $json_data = json_decode($raw_input, true);
    if (is_array($json_data)) {
        $_POST = array_merge($_POST, $json_data);
    }
}

// Old school helper functions
function clean_input($data) {
    global $conn;
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return mysqli_real_escape_string($conn, $data);
}

function is_logged_in() {
    if (isset($_SESSION['user_id']) && !empty($_SESSION['user_id'])) {
        return true;
    }
    return false;
}

function redirect($url) {
    header("Location: " . $url);
    exit();
}
?>
