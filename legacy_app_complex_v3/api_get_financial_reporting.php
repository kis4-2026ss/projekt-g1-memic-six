<?php
// API: Financial and Operational Performance Reporting (Analytics Subqueries)
header("Content-Type: application/json");
include('db.php');
include('functions.php');

$groupBy = isset($_GET['group_by']) ? sanitize_input($_GET['group_by']) : 'country'; // default group by country

if ($groupBy !== 'country' && $groupBy !== 'category') {
    http_response_code(400);
    echo json_encode(["error" => "Invalid group_by parameter. Must be 'country' or 'category'."]);
    mysqli_close($conn);
    exit;
}

$response = [
    "status" => "success",
    "timestamp" => date('Y-m-d H:i:s'),
    "group_by" => $groupBy,
    "metrics" => []
];

try {
    if ($groupBy === 'country') {
        // Complex query calculating total orders, revenue, shipping costs, and average order value by country
        $query = "SELECT 
                    c.country,
                    COUNT(o.id) AS total_orders,
                    COALESCE(SUM(o.total_amount), 0.00) AS total_sales,
                    COALESCE(SUM(o.shipping_cost), 0.00) AS total_shipping_revenue,
                    COALESCE(AVG(o.total_amount), 0.00) AS average_order_value,
                    (
                        SELECT COALESCE(SUM(oi.quantity), 0)
                        FROM order_items oi
                        INNER JOIN orders ord ON oi.order_id = ord.id
                        INNER JOIN customers cust ON ord.customer_id = cust.id
                        WHERE cust.country = c.country
                    ) AS total_items_sold
                  FROM customers c
                  LEFT JOIN orders o ON c.id = o.customer_id
                  GROUP BY c.country
                  ORDER BY total_sales DESC";
                  
        $result = mysqli_query($conn, $query);
        if (!$result) {
            throw new Exception("Country reporting query failed: " . mysqli_error($conn));
        }
        
        while ($row = mysqli_fetch_assoc($result)) {
            $row['total_orders'] = intval($row['total_orders']);
            $row['total_sales'] = floatval($row['total_sales']);
            $row['total_shipping_revenue'] = floatval($row['total_shipping_revenue']);
            $row['average_order_value'] = floatval($row['average_order_value']);
            $row['total_items_sold'] = intval($row['total_items_sold']);
            $response['metrics'][] = $row;
        }
    } else {
        // Complex query grouping sales and items by product category
        $query = "SELECT 
                    p.category,
                    COUNT(DISTINCT oi.order_id) AS orders_count,
                    COALESCE(SUM(oi.quantity), 0) AS total_quantity_sold,
                    COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 0.00) AS category_revenue,
                    COALESCE(AVG(oi.unit_price * (1 - oi.discount)), 0.00) AS average_item_price
                  FROM products p
                  LEFT JOIN order_items oi ON p.id = oi.product_id
                  GROUP BY p.category
                  ORDER BY category_revenue DESC";
                  
        $result = mysqli_query($conn, $query);
        if (!$result) {
            throw new Exception("Category reporting query failed: " . mysqli_error($conn));
        }
        
        while ($row = mysqli_fetch_assoc($result)) {
            $row['orders_count'] = intval($row['orders_count']);
            $row['total_quantity_sold'] = intval($row['total_quantity_sold']);
            $row['category_revenue'] = floatval($row['category_revenue']);
            $row['average_item_price'] = floatval($row['average_item_price']);
            $response['metrics'][] = $row;
        }
    }
    
    // Add overall high-level KPIs as a nested subquery result
    $kpiQuery = "SELECT 
                    (SELECT COUNT(*) FROM orders) AS kpi_total_orders,
                    (SELECT COALESCE(SUM(total_amount), 0.00) FROM orders) AS kpi_total_revenue,
                    (SELECT COALESCE(SUM(shipping_cost), 0.00) FROM orders) AS kpi_total_shipping,
                    (SELECT COUNT(*) FROM customers WHERE status = 'active') AS kpi_active_customers,
                    (SELECT COUNT(*) FROM shipments WHERE status = 'in_transit') AS kpi_shipments_in_transit";
                    
    $kpiResult = mysqli_query($conn, $kpiQuery);
    if ($kpiResult) {
        $kpi = mysqli_fetch_assoc($kpiResult);
        $response['global_kpis'] = [
            "total_orders" => intval($kpi['kpi_total_orders']),
            "total_revenue" => floatval($kpi['kpi_total_revenue']),
            "total_shipping" => floatval($kpi['kpi_total_shipping']),
            "active_customers" => intval($kpi['kpi_active_customers']),
            "shipments_in_transit" => intval($kpi['kpi_shipments_in_transit'])
        ];
    }

    echo json_encode($response);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "status" => "error",
        "message" => $e->getMessage()
    ]);
}

mysqli_close($conn);
?>
