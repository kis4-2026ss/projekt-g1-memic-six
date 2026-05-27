<?php
// API: Process Order Fulfillment & Shipping (State Machine Transaction)
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

$orderId = isset($inputData['order_id']) ? intval($inputData['order_id']) : null;
$carrier = isset($inputData['carrier']) ? sanitize_input($inputData['carrier']) : null;
$trackingNumber = isset($inputData['tracking_number']) ? sanitize_input($inputData['tracking_number']) : null;
$userId = isset($inputData['user_id']) ? intval($inputData['user_id']) : null;

if (!$orderId || !$carrier || !$trackingNumber) {
    http_response_code(400);
    echo json_encode(["error" => "Missing order_id, carrier, or tracking_number"]);
    mysqli_close($conn);
    exit;
}

// 1. Fetch Order and Verify Status
$orderQuery = "SELECT id, status, customer_id FROM orders WHERE id = " . $orderId . " FOR UPDATE";
$orderRes = mysqli_query($conn, $orderQuery);
$order = mysqli_fetch_assoc($orderRes);

if (!$order) {
    http_response_code(404);
    echo json_encode(["error" => "Order not found"]);
    mysqli_close($conn);
    exit;
}

if ($order['status'] !== 'pending') {
    http_response_code(400);
    echo json_encode(["error" => "Only 'pending' orders can be fulfilled. Current status is: " . $order['status']]);
    mysqli_close($conn);
    exit;
}

// 2. Start Fulfillment Transaction
mysqli_begin_transaction($conn);

try {
    // 3. Process Inventory Reductions (Deduct from reserved and actual stock)
    $itemsQuery = "SELECT oi.product_id, oi.quantity, p.name 
                   FROM order_items oi 
                   INNER JOIN products p ON oi.product_id = p.id
                   WHERE oi.order_id = " . $orderId;
    $itemsRes = mysqli_query($conn, $itemsQuery);
    
    while ($item = mysqli_fetch_assoc($itemsRes)) {
        $productId = intval($item['product_id']);
        $quantity = intval($item['quantity']);
        
        // Find where this product has reserved quantities
        $invQuery = "SELECT id, stock_qty, reserved_qty 
                     FROM inventory 
                     WHERE product_id = $productId AND reserved_qty >= $quantity 
                     LIMIT 1 FOR UPDATE";
        $invRes = mysqli_query($conn, $invQuery);
        $inventoryRow = mysqli_fetch_assoc($invRes);
        
        if (!$inventoryRow) {
            throw new Exception("Stock deduction error: Missing reserved stock for product " . $item['name']);
        }
        
        // Deduct quantities: Decrease both stock_qty and reserved_qty
        $invUpdate = "UPDATE inventory 
                      SET stock_qty = stock_qty - $quantity,
                          reserved_qty = reserved_qty - $quantity
                      WHERE id = " . $inventoryRow['id'];
        $invUpdateRes = mysqli_query($conn, $invUpdate);
        
        if (!$invUpdateRes) {
            throw new Exception("Failed to deduct inventory stock: " . mysqli_error($conn));
        }
    }
    
    // 4. Update Order Status (Transition state to 'shipped')
    $orderUpdate = "UPDATE orders SET status = 'shipped' WHERE id = " . $orderId;
    $orderUpdateRes = mysqli_query($conn, $orderUpdate);
    
    if (!$orderUpdateRes) {
        throw new Exception("Failed to update order status: " . mysqli_error($conn));
    }
    
    // 5. Create Shipment Record
    $shipDate = date('Y-m-d');
    $shipmentInsert = "INSERT INTO shipments (order_id, carrier, tracking_number, ship_date, status) 
                       VALUES ($orderId, '$carrier', '$trackingNumber', '$shipDate', 'in_transit')";
    $shipmentInsertRes = mysqli_query($conn, $shipmentInsert);
    
    if (!$shipmentInsertRes) {
        throw new Exception("Failed to create shipment record: " . mysqli_error($conn));
    }
    
    $shipmentId = mysqli_insert_id($conn);
    
    // Log Audit Trail
    log_audit_action($conn, $userId, "FULFILL_ORDER", "orders", $orderId, "Fulfilled order. Status changed to shipped. Shipment ID: $shipmentId. Carrier: $carrier, Tracking: $trackingNumber.");
    
    // Commit Transaction
    mysqli_commit($conn);
    
    echo json_encode([
        "status" => "success",
        "message" => "Order fulfilled successfully. Shipments dispatched.",
        "order_id" => $orderId,
        "shipment" => [
            "shipment_id" => $shipmentId,
            "carrier" => $carrier,
            "tracking_number" => $trackingNumber,
            "ship_date" => $shipDate,
            "shipment_status" => "in_transit"
        ]
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
