<?php
require_once('db.php');
require_once('functions.php');
include('header.php');

if (!is_logged_in() || $_SESSION['role'] !== 'admin') {
    die("<h2 class='error'>Access Denied: Admins Only!</h2>");
}

if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['update_stock'])) {
    $product_id = (int)$_POST['product_id'];
    $new_stock = (int)$_POST['new_stock'];
    
    $update_q = "UPDATE products SET stock = $new_stock WHERE id = $product_id";
    if (mysqli_query($conn, $update_q)) {
        echo "<p class='success'>Stock updated successfully!</p>";
    } else {
        echo "<p class='error'>Error updating stock.</p>";
    }
}
?>
<h2>Admin Control Panel</h2>
<h3>Inventory Management</h3>
<table border="1">
    <tr><th>ID</th><th>Name</th><th>Price</th><th>Current Stock</th><th>Update Stock</th></tr>
    <?php
    $res = mysqli_query($conn, "SELECT * FROM products ORDER BY id DESC");
    while($row = mysqli_fetch_assoc($res)) {
        echo "<tr>";
        echo "<td>" . $row['id'] . "</td>";
        echo "<td>" . htmlspecialchars($row['name']) . "</td>";
        echo "<td>$" . number_format($row['price'], 2) . "</td>";
        echo "<td>" . $row['stock'] . "</td>";
        echo "<td>
                <form method='POST' action='' style='margin:0;'>
                    <input type='hidden' name='product_id' value='" . $row['id'] . "'>
                    <input type='number' name='new_stock' value='" . $row['stock'] . "' style='width:60px;'>
                    <input type='submit' name='update_stock' value='Save'>
                </form>
              </td>";
        echo "</tr>";
    }
    ?>
</table>

<h3>Recent System Logs</h3>
<textarea style="width: 100%; height: 200px; background: #000; color: #0f0; font-family: monospace;" readonly>
<?php
$logfile = __DIR__ . '/app_log.txt';
if (file_exists($logfile)) {
    // Reading file completely into memory (bad practice, typical legacy)
    echo htmlspecialchars(file_get_contents($logfile));
} else {
    echo "No logs found.";
}
?>
</textarea>

<?php include('footer.php'); ?>
