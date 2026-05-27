<?php
session_start();
require_once('db.php');
require_once('functions.php');

if (!is_logged_in()) {
    redirect('login.php');
}

$user_id = $_SESSION['user_id'];
$status_filter = isset($_GET['status']) ? clean_input($_GET['status']) : 'all';

$query = "SELECT o.id as order_id, o.order_date, o.total_amount, o.status, p.name as product_name 
          FROM orders o 
          LEFT JOIN order_items oi ON o.id = oi.order_id
          LEFT JOIN products p ON oi.product_id = p.id 
          WHERE o.user_id = $user_id";

if ($status_filter != 'all') {
    $query .= " AND o.status = '$status_filter'";
}

$query .= " ORDER BY o.order_date DESC";

$result = mysqli_query($conn, $query);
?>
<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body>
    <h1>Welcome, <?php echo htmlspecialchars($_SESSION['username']); ?>!</h1>
    <a href="logout.php">Logout</a>
    
    <h2>Your Orders</h2>
    <form method="GET" action="dashboard.php">
        <select name="status">
            <option value="all" <?php if($status_filter == 'all') echo 'selected'; ?>>All</option>
            <option value="pending" <?php if($status_filter == 'pending') echo 'selected'; ?>>Pending</option>
            <option value="shipped" <?php if($status_filter == 'shipped') echo 'selected'; ?>>Shipped</option>
        </select>
        <input type="submit" value="Filter">
    </form>
    
    <table border="1">
        <tr>
            <th>Order ID</th>
            <th>Product</th>
            <th>Date</th>
            <th>Amount</th>
            <th>Status</th>
        </tr>
        <?php
        if (mysqli_num_rows($result) > 0) {
            while($row = mysqli_fetch_assoc($result)) {
                echo "<tr>";
                echo "<td>" . htmlspecialchars($row['order_id']) . "</td>";
                echo "<td>" . htmlspecialchars($row['product_name']) . "</td>";
                echo "<td>" . htmlspecialchars($row['order_date']) . "</td>";
                echo "<td>$" . number_format($row['total_amount'], 2) . "</td>";
                echo "<td>" . htmlspecialchars($row['status']) . "</td>";
                echo "</tr>";
            }
        } else {
            echo "<tr><td colspan='5'>No orders found.</td></tr>";
        }
        ?>
    </table>
</body>
</html>
