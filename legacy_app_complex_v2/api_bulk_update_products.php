<?php
// API Bulk Update Products - Transactional Upsert
header('Content-Type: application/json');
include('db.php');
include('functions.php');

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    echo json_encode(["success" => false, "error" => "Invalid JSON input"]);
    exit;
}

$user_id = isset($data['user_id']) ? intval($data['user_id']) : 1;
$products = isset($data['products']) ? $data['products'] : [];

if (empty($products)) {
    echo json_encode(["success" => false, "error" => "No products list provided"]);
    exit;
}

// -------------------------------------------------------------------------
// START TRANSACTION
// -------------------------------------------------------------------------
mysqli_begin_transaction($conn);

try {
    $inserted = 0;
    $updated = 0;
    
    foreach ($products as $prod) {
        $sku = mysqli_real_escape_string($conn, $prod['sku']);
        $name = mysqli_real_escape_string($conn, $prod['name']);
        $price = floatval($prod['unit_price']);
        
        if (empty($sku) || empty($name) || $price < 0) {
            throw new Exception("Validation Error: Invalid sku, name or unit_price in product bulk list.");
        }
        
        // Check if product already exists
        $check_query = "SELECT id FROM products WHERE sku = '$sku' FOR UPDATE";
        $check_res = mysqli_query($conn, $check_query);
        
        if ($check_res && mysqli_num_rows($check_res) > 0) {
            // Update existing product
            $update_query = "
                UPDATE products 
                SET name = '$name', unit_price = $price 
                WHERE sku = '$sku'
            ";
            if (!mysqli_query($conn, $update_query)) {
                throw new Exception("Failed to update product '$sku': " . mysqli_error($conn));
            }
            $updated++;
        } else {
            // Insert new product
            $insert_query = "
                INSERT INTO products (sku, name, unit_price) 
                VALUES ('$sku', '$name', $price)
            ";
            if (!mysqli_query($conn, $insert_query)) {
                throw new Exception("Failed to insert product '$sku': " . mysqli_error($conn));
            }
            $inserted++;
        }
    }
    
    // Log Bulk Action
    log_action($user_id, 'BULK_UPSERT_PRODUCTS', 'products', NULL, "Bulk upsert completed. Inserted: $inserted, Updated: $updated", $conn);
    
    // -------------------------------------------------------------------------
    // COMMIT TRANSACTION
    // -------------------------------------------------------------------------
    mysqli_commit($conn);
    
    echo json_encode([
        "success" => true,
        "inserted" => $inserted,
        "updated" => $updated
    ]);
    
} catch (Exception $e) {
    // -------------------------------------------------------------------------
    // ROLLBACK TRANSACTION
    // -------------------------------------------------------------------------
    mysqli_rollback($conn);
    echo json_encode(["success" => false, "error" => $e->getMessage()]);
}

mysqli_close($conn);
?>
