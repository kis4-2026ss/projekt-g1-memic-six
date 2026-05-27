<?php
// API: Get Inventory Status and Capacity Alerts Across Warehouses
header("Content-Type: application/json");
include('db.php');
include('functions.php');

$warehouseId = isset($_GET['warehouse_id']) ? intval($_GET['warehouse_id']) : null;
$category = isset($_GET['category']) ? sanitize_input($_GET['category']) : null;

// Complex query with JOINs, calculations, and grouping
$query = "SELECT 
            i.id AS inventory_id,
            w.id AS warehouse_id,
            w.code AS warehouse_code,
            w.name AS warehouse_name,
            w.city AS warehouse_city,
            p.id AS product_id,
            p.sku AS product_sku,
            p.name AS product_name,
            p.category AS product_category,
            p.unit_price,
            i.stock_qty,
            i.reserved_qty,
            (i.stock_qty - i.reserved_qty) AS available_qty,
            i.reorder_level,
            CASE 
                WHEN (i.stock_qty - i.reserved_qty) <= 0 THEN 'OUT_OF_STOCK'
                WHEN (i.stock_qty - i.reserved_qty) <= i.reorder_level THEN 'LOW_STOCK'
                ELSE 'OK'
            END AS stock_status
          FROM inventory i
          INNER JOIN warehouses w ON i.warehouse_id = w.id
          INNER JOIN products p ON i.product_id = p.id
          WHERE 1=1";

if ($warehouseId) {
    $query .= " AND w.id = " . $warehouseId;
}

if ($category) {
    $query .= " AND p.category = '" . mysqli_real_escape_string($conn, $category) . "'";
}

$query .= " ORDER BY w.code ASC, stock_status DESC, available_qty ASC";

$result = mysqli_query($conn, $query);

if (!$result) {
    http_response_code(500);
    echo json_encode(["error" => "Inventory fetch failed: " . mysqli_error($conn)]);
    mysqli_close($conn);
    exit;
}

$inventory = [];
$lowStockAlertsCount = 0;
$outOfStockAlertsCount = 0;
$totalInventoryValue = 0.00;

while ($row = mysqli_fetch_assoc($result)) {
    // Math operations
    $row['stock_qty'] = intval($row['stock_qty']);
    $row['reserved_qty'] = intval($row['reserved_qty']);
    $row['available_qty'] = intval($row['available_qty']);
    $row['reorder_level'] = intval($row['reorder_level']);
    $row['unit_price'] = floatval($row['unit_price']);
    $row['inventory_value'] = $row['stock_qty'] * $row['unit_price'];
    
    $totalInventoryValue += $row['inventory_value'];
    
    if ($row['stock_status'] === 'LOW_STOCK') {
        $lowStockAlertsCount++;
    } elseif ($row['stock_status'] === 'OUT_OF_STOCK') {
        $outOfStockAlertsCount++;
    }
    
    $inventory[] = $row;
}

// Calculate Warehouse capacity occupation helper
$capacityQuery = "SELECT 
                    w.id, 
                    w.code, 
                    w.capacity_sqft, 
                    COALESCE(SUM(i.stock_qty), 0) as total_units_stored,
                    ROUND((COALESCE(SUM(i.stock_qty), 0) / w.capacity_sqft) * 100, 2) as utilization_percentage
                  FROM warehouses w
                  LEFT JOIN inventory i ON w.id = i.warehouse_id
                  GROUP BY w.id";
$capacityResult = mysqli_query($conn, $capacityQuery);
$warehouseCapacity = [];
while ($capacityRow = mysqli_fetch_assoc($capacityResult)) {
    $capacityRow['capacity_sqft'] = intval($capacityRow['capacity_sqft']);
    $capacityRow['total_units_stored'] = intval($capacityRow['total_units_stored']);
    $capacityRow['utilization_percentage'] = floatval($capacityRow['utilization_percentage']);
    $warehouseCapacity[] = $capacityRow;
}

$response = [
    "status" => "success",
    "timestamp" => date('Y-m-d H:i:s'),
    "filters" => [
        "warehouse_id" => $warehouseId,
        "category" => $category
    ],
    "summary" => [
        "total_items_tracked" => count($inventory),
        "total_inventory_value" => $totalInventoryValue,
        "low_stock_alerts" => $lowStockAlertsCount,
        "out_of_stock_alerts" => $outOfStockAlertsCount
    ],
    "warehouse_capacity" => $warehouseCapacity,
    "inventory" => $inventory
];

echo json_encode($response);
mysqli_close($conn);
?>
