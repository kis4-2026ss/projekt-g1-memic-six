<?php
session_start();
require_once('db.php');
require_once('functions.php');

if (!is_logged_in()) {
    die("Unauthorized access.");
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $user_id = $_SESSION['user_id'];
    $product_id = (int)$_POST['product_id'];
    $quantity = (int)$_POST['quantity'];
    
    // Check product price and stock
    $prod_query = "SELECT price, stock FROM products WHERE id = $product_id";
    $prod_result = mysqli_query($conn, $prod_query);
    $product = mysqli_fetch_assoc($prod_result);
    
    if ($product && $product['stock'] >= $quantity) {
        $total = $product['price'] * $quantity;
        $date = date('Y-m-d H:i:s');
        
        // Insert order
        $insert_query = "INSERT INTO orders (user_id, product_id, quantity, total_amount, order_date, status) 
                         VALUES ($user_id, $product_id, $quantity, $total, '$date', 'pending')";
                         
        if (mysqli_query($conn, $insert_query)) {
            // Update stock
            $new_stock = $product['stock'] - $quantity;
            mysqli_query($conn, "UPDATE products SET stock = $new_stock WHERE id = $product_id");
            
            redirect('dashboard.php?msg=order_success');
        } else {
            echo "Error placing order: " . mysqli_error($conn);
        }
    } else {
        echo "Product unavailable or insufficient stock.";
    }
} else {
    echo "Invalid request.";
}
?>
