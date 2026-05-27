<?php
// Page: Warehouse ERP Administrative Dashboard Control Board
include('db.php');
include('functions.php');

// Fetch global dashboard counts
$whCountQuery = "SELECT COUNT(*) as count FROM warehouses";
$whCountResult = mysqli_query($conn, $whCountQuery);
$whCount = mysqli_fetch_assoc($whCountResult)['count'];

$prodCountQuery = "SELECT COUNT(*) as count FROM products";
$prodCountResult = mysqli_query($conn, $prodCountQuery);
$prodCount = mysqli_fetch_assoc($prodCountResult)['count'];

$custCountQuery = "SELECT COUNT(*) as count FROM customers";
$custCountResult = mysqli_query($conn, $custCountQuery);
$custCount = mysqli_fetch_assoc($custCountResult)['count'];

$orderCountQuery = "SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0.00) as total_val FROM orders";
$orderCountResult = mysqli_query($conn, $orderCountQuery);
$orderCountData = mysqli_fetch_assoc($orderCountResult);
$orderCount = $orderCountData['count'];
$orderTotalVal = floatval($orderCountData['total_val']);

// Fetch low stock items alerts
$lowStockQuery = "SELECT 
                    w.name as warehouse_name, 
                    p.sku, 
                    p.name as product_name, 
                    i.stock_qty, 
                    i.reserved_qty, 
                    i.reorder_level
                  FROM inventory i
                  INNER JOIN warehouses w ON i.warehouse_id = w.id
                  INNER JOIN products p ON i.product_id = p.id
                  WHERE (i.stock_qty - i.reserved_qty) <= i.reorder_level
                  ORDER BY (i.stock_qty - i.reserved_qty) ASC
                  LIMIT 5";
$lowStockResult = mysqli_query($conn, $lowStockQuery);

// Fetch recent dispatch shipments pipeline
$recentShipmentsQuery = "SELECT 
                            s.tracking_number, 
                            s.carrier, 
                            s.ship_date, 
                            s.status,
                            o.total_amount,
                            c.name as customer_name
                          FROM shipments s
                          INNER JOIN orders o ON s.order_id = o.id
                          INNER JOIN customers c ON o.customer_id = c.id
                          ORDER BY s.ship_date DESC
                          LIMIT 5";
$recentShipmentsResult = mysqli_query($conn, $recentShipmentsQuery);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Warehouse ERP Admin Panel</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { background-color: #1e3a8a; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        h1 { margin: 0; font-size: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #3b82f6; }
        .stat-card.revenue { border-left-color: #10b981; }
        .stat-card h3 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #6b7280; }
        .stat-card p { margin: 0; font-size: 28px; font-weight: bold; color: #111827; }
        .main-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .panel h2 { margin-top: 0; font-size: 18px; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px; color: #1e3a8a; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 10px; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
        th { background-color: #f9fafb; color: #4b5563; font-weight: 600; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: bold; }
        .badge.danger { background-color: #fee2e2; color: #991b1b; }
        .badge.warning { background-color: #fef3c7; color: #92400e; }
        .badge.success { background-color: #d1fae5; color: #065f46; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>Warehouse ERP Control Center</h1>
                <p style="margin: 5px 0 0 0; font-size: 14px; color: #93c5fd;">System Status: Operations Active</p>
            </div>
            <div>
                <span style="font-size: 14px; background-color: #3b82f6; padding: 8px 12px; border-radius: 4px; font-weight: bold;">User: Administrator</span>
            </div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Warehouses</h3>
                <p><?php echo $whCount; ?></p>
            </div>
            <div class="stat-card">
                <h3>Tracked Products</h3>
                <p><?php echo $prodCount; ?></p>
            </div>
            <div class="stat-card">
                <h3>Customer Accounts</h3>
                <p><?php echo $custCount; ?></p>
            </div>
            <div class="stat-card revenue">
                <h3>Total Sales Revenue</h3>
                <p>&euro; <?php echo number_format($orderTotalVal, 2); ?></p>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <h2>Low Stock & Capacity Alerts</h2>
                <?php if (mysqli_num_rows($lowStockResult) > 0): ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Warehouse</th>
                                <th>SKU</th>
                                <th>Product</th>
                                <th>Stock</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php while ($row = mysqli_fetch_assoc($lowStockResult)): 
                                $avail = intval($row['stock_qty']) - intval($row['reserved_qty']);
                                $statusClass = $avail <= 0 ? 'danger' : 'warning';
                                $statusLabel = $avail <= 0 ? 'OUT' : 'LOW';
                            ?>
                                <tr>
                                    <td><?php echo htmlspecialchars($row['warehouse_name']); ?></td>
                                    <td><code><?php echo htmlspecialchars($row['sku']); ?></code></td>
                                    <td><?php echo htmlspecialchars($row['product_name']); ?></td>
                                    <td><?php echo $avail; ?> / <?php echo $row['stock_qty']; ?></td>
                                    <td><span class="badge <?php echo $statusClass; ?>"><?php echo $statusLabel; ?></span></td>
                                </tr>
                            <?php endwhile; ?>
                        </tbody>
                    </table>
                <?php else: ?>
                    <p style="color: #6b7280; font-size: 14px;">All warehouse inventory levels are healthy!</p>
                <?php endif; ?>
            </div>
            
            <div class="panel">
                <h2>Recent Dispatched Shipments</h2>
                <?php if (mysqli_num_rows($recentShipmentsResult) > 0): ?>
                    <table>
                        <thead>
                            <tr>
                                <th>Tracking #</th>
                                <th>Customer</th>
                                <th>Carrier</th>
                                <th>Amount</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php while ($row = mysqli_fetch_assoc($recentShipmentsResult)): ?>
                                <tr>
                                    <td><code><?php echo htmlspecialchars($row['tracking_number']); ?></code></td>
                                    <td><?php echo htmlspecialchars($row['customer_name']); ?></td>
                                    <td><?php echo htmlspecialchars($row['carrier']); ?></td>
                                    <td>&euro; <?php echo number_format($row['total_amount'], 2); ?></td>
                                    <td><span class="badge success"><?php echo strtoupper(str_replace('_', ' ', $row['status'])); ?></span></td>
                                </tr>
                            <?php endwhile; ?>
                        </tbody>
                    </table>
                <?php else: ?>
                    <p style="color: #6b7280; font-size: 14px;">No shipments dispatched yet.</p>
                <?php endif; ?>
            </div>
        </div>
    </div>
</body>
</html>
<?php
mysqli_close($conn);
?>
