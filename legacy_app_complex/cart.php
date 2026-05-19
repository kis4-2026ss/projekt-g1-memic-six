<?php
require_once('db.php');
require_once('functions.php');
include('header.php');

if (!isset($_SESSION['cart'])) {
    $_SESSION['cart'] = array();
}

// Handle add to cart
if (isset($_GET['action']) && $_GET['action'] == 'add' && isset($_GET['id'])) {
    $product_id = (int)$_GET['id'];
    $qty = isset($_POST['qty']) ? (int)$_POST['qty'] : 1;
    
    if (isset($_SESSION['cart'][$product_id])) {
        $_SESSION['cart'][$product_id] += $qty;
    } else {
        $_SESSION['cart'][$product_id] = $qty;
    }
    echo "<p class='success'>Item added to cart.</p>";
}

// Handle clear cart
if (isset($_GET['action']) && $_GET['action'] == 'clear') {
    $_SESSION['cart'] = array();
    echo "<p class='success'>Cart cleared.</p>";
}

?>
<h2>Your Shopping Cart</h2>
<?php
if (empty($_SESSION['cart'])) {
    echo "<p>Your cart is empty.</p>";
} else {
    echo "<table border='1'><tr><th>Product</th><th>Price</th><th>Quantity</th><th>Subtotal</th></tr>";
    $total = 0;
    
    foreach ($_SESSION['cart'] as $p_id => $qty) {
        $q = "SELECT name, price FROM products WHERE id = $p_id";
        $r = mysqli_query($conn, $q);
        if ($row = mysqli_fetch_assoc($r)) {
            $subtotal = $row['price'] * $qty;
            $total += $subtotal;
            echo "<tr>";
            echo "<td>" . htmlspecialchars($row['name']) . "</td>";
            echo "<td>$" . number_format($row['price'], 2) . "</td>";
            echo "<td>$qty</td>";
            echo "<td>$" . number_format($subtotal, 2) . "</td>";
            echo "</tr>";
        }
    }
    echo "<tr><td colspan='3' align='right'><strong>Total:</strong></td><td><strong>$" . number_format($total, 2) . "</strong></td></tr>";
    echo "</table><br>";
    echo "<a href='cart.php?action=clear'>Clear Cart</a> | ";
    if (is_logged_in()) {
        echo "<a href='checkout.php'>Proceed to Checkout</a>";
    } else {
        echo "<a href='login.php'>Login to Checkout</a>";
    }
}
?>

<h3>Available Products</h3>
<table border="1">
    <tr><th>Name</th><th>Price</th><th>Stock</th><th>Action</th></tr>
    <?php
    $prod_q = "SELECT id, name, price, stock FROM products WHERE stock > 0";
    $prod_r = mysqli_query($conn, $prod_q);
    while($p = mysqli_fetch_assoc($prod_r)) {
        echo "<tr>";
        echo "<td>" . htmlspecialchars($p['name']) . "</td>";
        echo "<td>$" . number_format($p['price'], 2) . "</td>";
        echo "<td>" . $p['stock'] . "</td>";
        echo "<td>
                <form method='POST' action='cart.php?action=add&id=" . $p['id'] . "'>
                    <input type='number' name='qty' value='1' min='1' max='" . $p['stock'] . "' style='width:50px;'>
                    <input type='submit' value='Add'>
                </form>
              </td>";
        echo "</tr>";
    }
    ?>
</table>

<?php include('footer.php'); ?>
