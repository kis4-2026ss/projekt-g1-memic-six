<?php
// API Get CRM KPIs - Advanced Relational Aggregations & Calculations
header('Content-Type: application/json');
include('db.php');
include('functions.php');

$userId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 1;

// 1. Get total companies count
$comp_res = mysqli_query($conn, "SELECT COUNT(*) AS total FROM companies");
$comp_data = mysqli_fetch_assoc($comp_res);
$total_companies = intval($comp_data['total']);

// 2. Get projects pipeline & win rate (completed vs total)
$proj_query = "
    SELECT 
        COUNT(*) AS total_projects,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_projects,
        SUM(budget) AS total_budget
    FROM projects
";
$proj_res = mysqli_query($conn, $proj_query);
$proj_data = mysqli_fetch_assoc($proj_res);
$total_projects = intval($proj_data['total_projects']);
$completed_projects = intval($proj_data['completed_projects']);
$total_budget = floatval($proj_data['total_budget']);

$win_rate = $total_projects > 0 ? round(($completed_projects / $total_projects) * 100, 2) : 0.00;

// 3. Get invoice balances (paid vs unpaid totals)
$inv_query = "
    SELECT 
        SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0.00 END) AS total_paid,
        SUM(CASE WHEN status = 'unpaid' THEN total_amount ELSE 0.00 END) AS total_unpaid
    FROM invoices
";
$inv_res = mysqli_query($conn, $inv_query);
$inv_data = mysqli_fetch_assoc($inv_res);
$total_paid = floatval($inv_data['total_paid']);
$total_unpaid = floatval($inv_data['total_unpaid']);

// 4. Get active MRR from active contracts
$contract_res = mysqli_query($conn, "SELECT SUM(monthly_recurring_revenue) AS active_mrr FROM contracts WHERE status = 'active'");
$contract_data = mysqli_fetch_assoc($contract_res);
$active_mrr = floatval($contract_data['active_mrr']);

// 5. Calculate a custom weighted ERP Health Score
// Weights: Win rate (40%), Debt control / unpaid-to-paid ratio (30%), Client scale (30%)
$debt_ratio = ($total_paid + $total_unpaid) > 0 ? ($total_unpaid / ($total_paid + $total_unpaid)) : 0;
$debt_score = max(0, 100 - ($debt_ratio * 100)); // 100 if no debt, 0 if all unpaid

$scale_score = min(100, $total_companies * 5); // 100 score if 20+ companies

$health_score = round(
    ($win_rate * 0.40) + 
    ($debt_score * 0.30) + 
    ($scale_score * 0.30), 
    2
);

// Log KPI retrieval
log_action($userId, 'GET_CRM_KPIS', 'analytics', NULL, "Generated weighted CRM KPIs. Health Score: $health_score", $conn);

echo json_encode([
    "success" => true,
    "kpis" => [
        "companies_count" => $total_companies,
        "projects" => [
            "total" => $total_projects,
            "completed" => $completed_projects,
            "win_rate_percentage" => $win_rate,
            "total_pipeline_budget" => $total_budget
        ],
        "financials" => [
            "total_invoiced_paid" => $total_paid,
            "outstanding_unpaid" => $total_unpaid,
            "monthly_recurring_revenue_mrr" => $active_mrr
        ],
        "system_health_score" => $health_score
    ]
]);

mysqli_close($conn);
?>
