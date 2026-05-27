<?php
// API: Bulk Inventory Adjustments and Stock Counts (Bulk Transaction Engine)
header("Content-Type: application/json");
include('db.php');
include('functions.php');

$inputData = json_decode(file_get_contents('php://input'), true);

if (!$inputData) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid JSON payload"]);
    mysqli_close($conn);
    exit;
}

$warehouseId = isset($inputData['warehouse_id']) ? intval($inputData['warehouse_id']) : null;
$userId = isset($inputData['user_id']) ? intval($inputData['user_id']) : null;
$adjustments = isset($inputData['adjustments']) ? $inputData['adjustments'] : [];

if (!$warehouseId || empty($adjustments)) {
    http_response_code(400);
    echo json_encode(["error" => "Missing warehouse_id or adjustments array"]);
    mysqli_close($conn);
    exit;
}

// Check permissions
$userRole = 'manager'; // Default role assumption for simple API test
if ($userId) {
    $userQuery = "SELECT role FROM users WHERE id = " . $userId;
    $userRes = mysqli_query($conn, $userQuery);
    if ($userRow = mysqli_fetch_assoc($userRes)) {
        $userRole = $userRow['role'];
    }
}

if (!check_permission($userRole, 'supervisor')) {
    http_response_code(403);
    echo json_encode(["error" => "Unauthorized. Supervisor role required for stock adjustments."]);
    mysqli_close($conn);
    exit;
}

// Start adjustment transaction
mysqli_begin_transaction($conn);

try {
    $processedCount = 0;
    
    foreach ($adjustments as $adj) {
        $productId = intval($adj['product_id']);
        $adjustmentQty = intval($adj['adjustment_qty']);
        
        if ($productId <= 0 || $adjustmentQty === 0) {
            continue; // Skip invalid rows
        }
        
        // Find existing inventory row
        $invQuery = "SELECT id, stock_qty, reserved_qty 
                     FROM inventory 
                     WHERE warehouse_id = $warehouseId AND product_id = $productId 
                     LIMIT 1 FOR UPDATE";
        $invRes = mysqli_query($conn, $invQuery);
        $inventoryRow = mysqli_fetch_assoc($invRes);
        
        if ($inventoryRow) {
            $newStock = $inventoryRow['stock_qty'] + $adjustmentQty;
            
            // Check that actual stock never falls below reserved quantities or below zero
            if ($newStock < intval($inventoryRow['reserved_qty'])) {
                throw new Exception("Adjustment failed. New stock level ($newStock) cannot be less than reserved stock (" . $inventoryRow['reserved_qty'] . ") for product ID: $productId");
            }
            if ($newStock < 0) {
                throw new Exception("Adjustment failed. New stock level cannot be negative for product ID: $productId");
            }
            
            // Perform stock level update
            $updateQuery = "UPDATE inventory 
                            SET stock_qty = $newStock 
                            WHERE id = " . $inventoryRow['id'];
            $updateRes = mysqli_query($conn, $updateQuery);
            if (!$updateRes) {
                throw new Exception("Failed to update inventory record: " . mysqli_error($conn));
            }
            
        } else {
            // No inventory row exists: if adjustment is negative, throw error
            if ($adjustmentQty < 0) {
                throw new Exception("Adjustment failed. Cannot deduct stock when no inventory record exists for product ID: $productId");
            }
            
            // Create a new inventory row
            $insertQuery = "INSERT INTO inventory (warehouse_id, product_id, stock_qty, reserved_qty, reorder_level) 
                            VALUES ($warehouseId, $productId, $adjustmentQty, 0, 10)";
            $insertRes = mysqli_query($conn, $insertQuery);
            if (!$insertRes) {
                throw new Exception("Failed to insert new inventory record: " . mysqli_error($conn));
            }
        }
        
        $processedCount++;
    }
    
    // Log audit trail
    log_audit_action($conn, $userId, "BULK_INVENTORY_ADJUST", "inventory", $warehouseId, "Processed batch stock adjustment for $processedCount items in warehouse $warehouseId.");
    
    // Commit transaction
    mysqli_commit($conn);
    
    echo json_encode([
        "status" => "success",
        "message" => "Successfully processed $processedCount inventory adjustments.",
        "warehouse_id" => $warehouseId,
        "items_updated" => $processedCount
    ]);

} catch (Exception $e) {
    // Rollback transaction
    mysqli_rollback($conn);
    
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => $e->getMessage()
    ]);
}

mysqli_close($conn);
?>
