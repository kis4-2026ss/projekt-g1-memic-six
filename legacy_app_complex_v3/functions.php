<?php
// Helper functions for Enterprise Warehouse Management System

// Audit Logging
function log_audit_action($conn, $userId, $action, $entityName, $entityId, $details) {
    $userIdSafe = $userId ? intval($userId) : 'NULL';
    $actionSafe = mysqli_real_escape_string($conn, $action);
    $entitySafe = mysqli_real_escape_string($conn, $entityName);
    $entityIdSafe = intval($entityId);
    $detailsSafe = mysqli_real_escape_string($conn, $details);

    $logQuery = "INSERT INTO audit_logs (user_id, action, entity_name, entity_id, details) 
                 VALUES ($userIdSafe, '$actionSafe', '$entitySafe', $entityIdSafe, '$detailsSafe')";
    mysqli_query($conn, $logQuery);
    
    // File-based logging backup
    $logMsg = "[" . date('Y-m-d H:i:s') . "] User $userIdSafe performed $actionSafe on $entitySafe (ID: $entityIdSafe). Details: $detailsSafe\n";
    file_put_contents(__DIR__ . '/erp_audit_log.txt', $logMsg, FILE_APPEND);
}

// Country-specific shipping fee calculator
function calculate_shipping_fee($country, $weightKg, $carrier) {
    $baseFee = 5.00;
    
    // weight multiplier
    $weightFee = $weightKg * 1.50;
    
    // Country adjustments
    $countryMultiplier = 1.0;
    $countryUpper = strtoupper($country);
    if ($countryUpper !== 'DE' && $countryUpper !== 'GERMANY') {
        if (in_array($countryUpper, ['FR', 'NL', 'AT', 'IT', 'ES'])) {
            $countryMultiplier = 2.5; // EU
        } else {
            $countryMultiplier = 5.0; // Rest of world
        }
    }
    
    // Carrier adjustments
    $carrierSurcharge = 0.00;
    if (strtoupper($carrier) === 'DHL_EXPRESS') {
        $carrierSurcharge = 12.00;
    } elseif (strtoupper($carrier) === 'FEDEX') {
        $carrierSurcharge = 8.50;
    }
    
    return ($baseFee + $weightFee) * $countryMultiplier + $carrierSurcharge;
}

// Input verification
function sanitize_input($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}

// Security Check
function check_permission($role, $requiredRole) {
    $rolesHierarchy = [
        'admin' => 3,
        'supervisor' => 2,
        'manager' => 1
    ];
    
    $userLevel = isset($rolesHierarchy[$role]) ? $rolesHierarchy[$role] : 0;
    $requiredLevel = isset($rolesHierarchy[$requiredRole]) ? $rolesHierarchy[$requiredRole] : 0;
    
    return $userLevel >= $requiredLevel;
}
?>
