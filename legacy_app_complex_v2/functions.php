<?php
// Procedural helpers and CRM utilities

function calculate_tax($amount, $tax_rate = 0.19) {
    if (!is_numeric($amount) || $amount < 0) {
        return 0;
    }
    return round($amount * $tax_rate, 2);
}

function format_currency($value) {
    return "€" . number_format($value, 2, ',', '.');
}

function check_user_permission($user_id, $required_role, $conn) {
    if (empty($user_id)) {
        return false;
    }
    
    $query = "SELECT role FROM users WHERE id = " . intval($user_id);
    $result = mysqli_query($conn, $query);
    
    if ($result && mysqli_num_rows($result) > 0) {
        $row = mysqli_fetch_assoc($result);
        if ($row['role'] === 'admin') {
            return true; // Admin override
        }
        return $row['role'] === $required_role;
    }
    return false;
}

function log_action($user_id, $action, $entity, $entity_id, $details, $conn) {
    $user_id_val = empty($user_id) ? 'NULL' : intval($user_id);
    $action_esc = mysqli_real_escape_string($conn, $action);
    $entity_esc = mysqli_real_escape_string($conn, $entity);
    $entity_id_val = empty($entity_id) ? 'NULL' : intval($entity_id);
    $details_esc = mysqli_real_escape_string($conn, $details);
    
    $query = "INSERT INTO audit_logs (user_id, action, entity_name, entity_id, details) 
              VALUES ($user_id_val, '$action_esc', '$entity_esc', $entity_id_val, '$details_esc')";
    
    return mysqli_query($conn, $query);
}
?>
