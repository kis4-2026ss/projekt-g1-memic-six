<?php
// Simple API endpoint serving JSON
require_once('db.php');

$category_id = isset($_GET['category']) ? (int)$_GET['category'] : 0;

$query = "SELECT id, name, price, stock, category_id FROM products WHERE stock > 0";
if ($category_id > 0) {
    // Insecure concatenation in API
    $query .= " AND category_id = " . $category_id;
}

$result = mysqli_query($conn, $query);

$products = array();
if ($result && mysqli_num_rows($result) > 0) {
    while($row = mysqli_fetch_assoc($result)) {
        // cast types correctly for JSON
        $row['id'] = (int)$row['id'];
        $row['price'] = (float)$row['price'];
        $row['stock'] = (int)$row['stock'];
        $row['category_id'] = (int)$row['category_id'];
        $products[] = $row;
    }
}

header('Content-Type: application/json');
echo json_encode(array(
    'success' => true,
    'count' => count($products),
    'data' => $products
));
?>
