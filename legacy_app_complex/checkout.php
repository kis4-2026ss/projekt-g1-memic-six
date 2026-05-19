<?php
require_once('db.php');
require_once('functions.php');
require_once('logger.php');
include('header.php');

if (!is_logged_in()) {
    redirect('login.php');
}

if (empty($_SESSION['cart'])) {
    echo "<p class='error'>Cart is empty. Cannot checkout.</p>";
    include('footer.php');
    exit;
}

if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['confirm_checkout'])) {
    $user_id = $_SESSION['user_id'];
    $date = date('Y-m-d H:i:s');
    $checkout_success = true;
    
    // Calculate total first
    $grand_total = 0;
    foreach ($_SESSION['cart'] as $p_id => $qty) {
        $q = "SELECT price FROM products WHERE id = $p_id";
        $r = mysqli_query($conn, $q);
        if ($row = mysqli_fetch_assoc($r)) {
            $grand_total += ($row['price'] * $qty);
        }
    }
    
    // Create main order record
    $order_q = "INSERT INTO orders (user_id, total_amount, order_date, status) VALUES ($user_id, $grand_total, '$date', 'pending')";
    if (mysqli_query($conn, $order_q)) {
        $order_id = mysqli_insert_id($conn); // Get the newly created order ID
        
        // Loop cart to create order_items and update stock (Simulating complex relational inserts)
        foreach ($_SESSION['cart'] as $p_id => $qty) {
            $q = "SELECT price, stock FROM products WHERE id = $p_id";
            $r = mysqli_query($conn, $q);
            if ($row = mysqli_fetch_assoc($r)) {
                if ($row['stock'] >= $qty) {
                    $price = $row['price'];
                    
                    // Insert item
                    $item_q = "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES ($order_id, $p_id, $qty, $price)";
                    mysqli_query($conn, $item_q);
                    
                    // Update stock
                    $new_stock = $row['stock'] - $qty;
                    mysqli_query($conn, "UPDATE products SET stock = $new_stock WHERE id = $p_id");
                } else {
                    $checkout_success = false;
                    log_event("Checkout failed for Order $order_id: Insufficient stock for product $p_id", "ERROR");
                }
            }
        }
        
        if ($checkout_success) {
            log_event("Order $order_id successfully created by User $user_id", "INFO");
            $_SESSION['cart'] = array(); // Empty cart
            echo "<h2>Checkout Successful!</h2>";
            echo "<p>Your order #$order_id has been placed.</p>";
        } else {
            echo "<h2>Checkout Partial Error</h2><p>Some items were out of stock.</p>";
        }
    } else {
        echo "<p class='error'>Failed to create order: " . mysqli_error($conn) . "</p>";
    }
} else {
    // Show confirmation page
    echo "<h2>Confirm Checkout</h2>";
    echo "<p>Are you sure you want to place the order for the items in your cart?</p>";
    echo "<form method='POST' action=''>";
    echo "<input type='hidden' name='confirm_checkout' value='1'>";
    echo "<input type='submit' value='Confirm Purchase'>";
    echo "</form>";
}

include('footer.php');
?>
