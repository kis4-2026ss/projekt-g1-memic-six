<?php
// API: Create Customer Order (Transaction and Inventory Reservation Engine)
header("Content-Type: application/json");
include('db.php');
include('functions.php');

// Parse request body
$inputData = json_decode(file_get_contents('php://input'), true);

if (!$inputData) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid JSON payload"]);
    mysqli_close($conn);
    exit;
}

$customerId = isset($inputData['customer_id']) ? intval($inputData['customer_id']) : null;
$createdBy = isset($inputData['created_by']) ? intval($inputData['created_by']) : null;
$items = isset($inputData['items']) ? $inputData['items'] : [];
$carrier = isset($inputData['carrier']) ? sanitize_input($inputData['carrier']) : 'DHL';

if (!$customerId || empty($items)) {
    http_response_code(400);
    echo json_encode(["error" => "Missing customer_id or items array"]);
    mysqli_close($conn);
    exit;
}

// 1. Verify customer status
$custQuery = "SELECT country, status FROM customers WHERE id = " . $customerId;
$custResult = mysqli_query($conn, $custQuery);
$customer = mysqli_fetch_assoc($custResult);

if (!$customer) {
    http_response_code(404);
    echo json_encode(["error" => "Customer not found"]);
    mysqli_close($conn);
    exit;
}

if ($customer['status'] !== 'active') {
    http_response_code(400);
    echo json_encode(["error" => "Customer account is inactive. Orders blocked."]);
    mysqli_close($conn);
    exit;
}

// 2. Start Transaction
mysqli_begin_transaction($conn);

$orderTotal = 0.00;
$totalWeight = 0.00;
$orderDetails = [];

try {
    // Process items first to calculate total weight and verify stock
    foreach ($items as $item) {
        $productId = intval($item['product_id']);
        $quantity = intval($item['quantity']);
        
        if ($productId <= 0 || $quantity <= 0) {
            throw new Exception("Invalid product ID or quantity");
        }
        
        // Fetch product info
        $prodQuery = "SELECT name, unit_price, weight_kg, category FROM products WHERE id = " . $productId;
        $prodRes = mysqli_query($conn, $prodQuery);
        $product = mysqli_fetch_assoc($prodRes);
        
        if (!$product) {
            throw new Exception("Product not found (ID: $productId)");
        }
        
        // Verify warehouse inventory (stock availability)
        // Find a warehouse with sufficient stock
        $invQuery = "SELECT id, warehouse_id, stock_qty, reserved_qty 
                     FROM inventory 
                     WHERE product_id = $productId AND (stock_qty - reserved_qty) >= $quantity 
                     LIMIT 1 FOR UPDATE"; // Locking rows
        $invRes = mysqli_query($conn, $invQuery);
        $inventoryRow = mysqli_fetch_assoc($invRes);
        
        if (!$inventoryRow) {
            throw new Exception("Insufficient available stock for product: " . $product['name'] . " (ID: $productId)");
        }
        
        $itemSubtotal = $product['unit_price'] * $quantity;
        $itemWeight = $product['weight_kg'] * $quantity;
        
        $orderTotal += $itemSubtotal;
        $totalWeight += $itemWeight;
        
        $orderDetails[] = [
            "product_id" => $productId,
            "warehouse_id" => intval($inventoryRow['warehouse_id']),
            "inventory_id" => intval($inventoryRow['id']),
            "quantity" => $quantity,
            "unit_price" => floatval($product['unit_price']),
            "subtotal" => $itemSubtotal
        ];
    }
    
    // Apply bulk order discount (10% discount on order items if subtotal exceeds 500)
    $discountRate = 0.00;
    if ($orderTotal > 500.00) {
        $discountRate = 0.10; // 10% discount
    }
    
    // Recalculate totals with discount
    $discountedTotal = 0.00;
    foreach ($orderDetails as &$orderDetail) {
        $orderDetail['discount'] = $discountRate;
        $orderDetail['discounted_price'] = $orderDetail['unit_price'] * (1 - $discountRate);
        $orderDetail['subtotal'] = $orderDetail['discounted_price'] * $orderDetail['quantity'];
        $discountedTotal += $orderDetail['subtotal'];
    }
    unset($orderDetail);
    
    $orderTotal = $discountedTotal;
    
    // Calculate Shipping fee
    $shippingCost = calculate_shipping_fee($customer['country'], $totalWeight, $carrier);
    $finalTotal = $orderTotal + $shippingCost;
    
    // 3. Create Order
    $createdByVal = $createdBy ? $createdBy : 'NULL';
    $orderInsert = "INSERT INTO orders (customer_id, status, total_amount, shipping_cost, created_by) 
                    VALUES ($customerId, 'pending', $finalTotal, $shippingCost, $createdByVal)";
    $orderInsertRes = mysqli_query($conn, $orderInsert);
    
    if (!$orderInsertRes) {
        throw new Exception("Failed to create order: " . mysqli_error($conn));
    }
    
    $orderId = mysqli_insert_id($conn);
    
    // 4. Create Order Items & Reserve Inventory
    foreach ($orderDetails as $detail) {
        $itemInsert = "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount) 
                       VALUES ($orderId, {$detail['product_id']}, {$detail['quantity']}, {$detail['unit_price']}, {$detail['discount']})";
        $itemInsertRes = mysqli_query($conn, $itemInsert);
        
        if (!$itemInsertRes) {
            throw new Exception("Failed to save order item: " . mysqli_error($conn));
        }
        
        // Reserve Stock: Increase reserved_qty
        $reserveUpdate = "UPDATE inventory 
                          SET reserved_qty = reserved_qty + {$detail['quantity']} 
                          WHERE id = {$detail['inventory_id']}";
        $reserveUpdateRes = mysqli_query($conn, $reserveUpdate);
        
        if (!$reserveUpdateRes) {
            throw new Exception("Failed to update inventory reservation: " . mysqli_error($conn));
        }
    }
    
    // Log audit trail
    log_audit_action($conn, $createdBy, "CREATE_ORDER", "orders", $orderId, "Created pending order for customer $customerId. Total: $finalTotal. Shipping: $shippingCost.");
    
    // Commit transaction
    mysqli_commit($conn);
    
    echo json_encode([
        "status" => "success",
        "message" => "Order successfully created and inventory reserved.",
        "order_id" => $orderId,
        "totals" => [
            "subtotal" => $orderTotal,
            "discount_applied" => ($discountRate * 100) . "%",
            "shipping_cost" => $shippingCost,
            "total_amount" => $finalTotal
        ]
    ]);

} catch (Exception $e) {
    // Rollback on errors
    mysqli_rollback($conn);
    
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => $e->getMessage()
    ]);
}

mysqli_close($conn);
?>
