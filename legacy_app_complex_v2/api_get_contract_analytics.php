<?php
// API Get Contract Analytics - Complex SQL bucketing & aggregates
header('Content-Type: application/json');
include('db.php');
include('functions.php');

$userId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 1;

// Complex Query: MRR aggregate reporting by department and company tier bucketed via CASE
$analytics_query = "
    SELECT 
        d.name AS department_name,
        c.status AS contract_status,
        SUM(c.monthly_recurring_revenue) AS total_mrr,
        COUNT(c.id) AS active_contracts_count,
        SUM(CASE WHEN comp.revenue > 10000000.00 THEN c.monthly_recurring_revenue ELSE 0.00 END) AS enterprise_mrr,
        SUM(CASE WHEN comp.revenue BETWEEN 1000000.00 AND 10000000.00 THEN c.monthly_recurring_revenue ELSE 0.00 END) AS midmarket_mrr,
        SUM(CASE WHEN comp.revenue < 1000000.00 THEN c.monthly_recurring_revenue ELSE 0.00 END) AS smb_mrr
    FROM contracts c
    INNER JOIN departments d ON c.department_id = d.id
    INNER JOIN companies comp ON c.company_id = comp.id
    GROUP BY d.name, c.status
    ORDER BY total_mrr DESC
";

$result = mysqli_query($conn, $analytics_query);

if (!$result) {
    echo json_encode(["success" => false, "error" => "Database query failed: " . mysqli_error($conn)]);
    exit;
}

$report = [];
$grand_total_mrr = 0.00;

while ($row = mysqli_fetch_assoc($result)) {
    $total_mrr = floatval($row['total_mrr']);
    $grand_total_mrr += $total_mrr;
    
    $report[] = [
        "department" => $row['department_name'],
        "status" => $row['contract_status'],
        "total_mrr" => $total_mrr,
        "contracts_count" => intval($row['active_contracts_count']),
        "tiers" => [
            "enterprise" => floatval($row['enterprise_mrr']),
            "midmarket" => floatval($row['midmarket_mrr']),
            "smb" => floatval($row['smb_mrr'])
        ]
    ];
}

// Track log
log_action($userId, 'GET_CONTRACT_ANALYTICS', 'contracts', NULL, "Generated contract analytics report. Grand total MRR: €$grand_total_mrr", $conn);

echo json_encode([
    "success" => true,
    "report" => $report,
    "grand_total_mrr" => $grand_total_mrr
]);

mysqli_close($conn);
?>
