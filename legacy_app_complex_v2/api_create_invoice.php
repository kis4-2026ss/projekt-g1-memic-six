<?php
// API Create Invoice - Uses Database Transactions
header('Content-Type: application/json');
include('db.php');
include('functions.php');

// Retrieve JSON body payload
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    echo json_encode(["success" => false, "error" => "Invalid JSON input"]);
    exit;
}

$user_id = isset($data['user_id']) ? intval($data['user_id']) : 1;
$project_id = intval($data['project_id']);
$invoice_number = mysqli_real_escape_string($conn, $data['invoice_number']);
$due_days = isset($data['due_days']) ? intval($data['due_days']) : 30;
$items = isset($data['items']) ? $data['items'] : [];

if (empty($project_id) || empty($invoice_number) || empty($items)) {
    echo json_encode(["success" => false, "error" => "Missing required fields: project_id, invoice_number, items"]);
    exit;
}

// Calculate dates
$issued_date = date('Y-m-d');
$due_date = date('Y-m-d', strtotime("+$due_days days"));

// -------------------------------------------------------------------------
// START TRANSACTION
// -------------------------------------------------------------------------
mysqli_begin_transaction($conn);

try {
    // 1. Create Invoice record (initial amounts are 0, calculated later)
    $insert_invoice = "
        INSERT INTO invoices (project_id, invoice_number, total_amount, tax_amount, status, issued_date, due_date)
        VALUES ($project_id, '$invoice_number', 0.00, 0.00, 'unpaid', '$issued_date', '$due_date')
    ";
    
    if (!mysqli_query($conn, $insert_invoice)) {
        throw new Exception("Failed to insert invoice: " . mysqli_error($conn));
    }
    
    $invoice_id = mysqli_insert_id($conn);
    
    $subtotal = 0.00;
    
    // 2. Loop and insert invoice line items
    foreach ($items as $item) {
        $desc = mysqli_real_escape_string($conn, $item['description']);
        $qty = floatval($item['quantity']);
        $price = floatval($item['unit_price']);
        $total = $qty * $price;
        $subtotal += $total;
        
        $insert_item = "
            INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total_price)
            VALUES ($invoice_id, '$desc', $qty, $price, $total)
        ";
        
        if (!mysqli_query($conn, $insert_item)) {
            throw new Exception("Failed to insert invoice line item: " . mysqli_error($conn));
        }
    }
    
    // 3. Compute final amounts using tax utility function
    $tax = calculate_tax($subtotal, 0.19);
    $total_amount = $subtotal + $tax;
    
    // 4. Update the parent invoice record
    $update_invoice = "
        UPDATE invoices 
        SET total_amount = $total_amount, tax_amount = $tax 
        WHERE id = $invoice_id
    ";
    
    if (!mysqli_query($conn, $update_invoice)) {
        throw new Exception("Failed to update final invoice totals: " . mysqli_error($conn));
    }
    
    // 5. Track in audit logs
    log_action($user_id, 'CREATE_INVOICE', 'invoices', $invoice_id, "Created invoice $invoice_number with total: €$total_amount", $conn);
    
    // -------------------------------------------------------------------------
    // COMMIT TRANSACTION
    // -------------------------------------------------------------------------
    mysqli_commit($conn);
    
    echo json_encode([
        "success" => true, 
        "invoice_id" => $invoice_id, 
        "invoice_number" => $invoice_number,
        "subtotal" => $subtotal, 
        "tax" => $tax, 
        "total" => $total_amount
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
