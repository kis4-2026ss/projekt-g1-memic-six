<?php
// CRM Dashboard - Complex SQL Joins & KPIs
include('db.php');
include('functions.php');

$userId = isset($_GET['manager_id']) ? $_GET['manager_id'] : 1;

// Check dashboard permission
if (!check_user_permission($userId, 'manager', $conn)) {
    die("ACCESS DENIED: Insufficient permissions for Manager Dashboard.");
}

// Query 1: Big spaghetti join to fetch projects, companies, assigned tasks, and contact names
$spaghetti_query = "
    SELECT 
        p.id AS project_id,
        p.name AS project_name,
        p.budget AS project_budget,
        p.status AS project_status,
        c.name AS company_name,
        c.industry AS company_industry,
        t.title AS task_title,
        t.priority AS task_priority,
        t.status AS task_status,
        CONCAT(con.first_name, ' ', con.last_name) AS contact_name
    FROM projects p
    INNER JOIN companies c ON p.company_id = c.id
    LEFT JOIN tasks t ON t.project_id = p.id
    LEFT JOIN contacts con ON t.assigned_contact_id = con.id
    ORDER BY p.created_at DESC, t.due_date ASC
";

$spaghetti_result = mysqli_query($conn, $spaghetti_query);

if (!$spaghetti_result) {
    die("Query error: " . mysqli_error($conn));
}

// Query 2: Aggregate query for CRM Dashboard KPIs
$kpi_query = "
    SELECT 
        COUNT(DISTINCT c.id) AS total_companies,
        COUNT(DISTINCT p.id) AS total_projects,
        SUM(p.budget) AS total_pipeline_value,
        AVG(p.budget) AS average_project_budget
    FROM companies c
    LEFT JOIN projects p ON p.company_id = c.id
";
$kpi_result = mysqli_query($conn, $kpi_query);
$kpis = mysqli_fetch_assoc($kpi_result);

// Audit logging
log_action($userId, 'VIEW_DASHBOARD', 'dashboard', NULL, 'Manager viewed the CRM Dashboard KPIs', $conn);
?>
<!DOCTYPE html>
<html>
<head>
    <title>CRM Enterprise Dashboard</title>
</head>
<body>
    <h1>Enterprise CRM & ERP Dashboard</h1>
    
    <div class="kpis">
        <h3>Total Companies: <?php echo intval($kpis['total_companies']); ?></h3>
        <h3>Total Projects: <?php echo intval($kpis['total_projects']); ?></h3>
        <h3>Pipeline Value: <?php echo format_currency($kpis['total_pipeline_value']); ?></h3>
        <h3>Average Budget: <?php echo format_currency($kpis['average_project_budget']); ?></h3>
    </div>
    
    <h2>Project & Task pipeline</h2>
    <table border="1">
        <thead>
            <tr>
                <th>Project Name</th>
                <th>Company</th>
                <th>Industry</th>
                <th>Budget</th>
                <th>Project Status</th>
                <th>Task Title</th>
                <th>Task Status</th>
                <th>Assigned Contact</th>
            </tr>
        </thead>
        <tbody>
            <?php while ($row = mysqli_fetch_assoc($spaghetti_result)): ?>
                <tr>
                    <td><?php echo htmlspecialchars($row['project_name']); ?></td>
                    <td><?php echo htmlspecialchars($row['company_name']); ?></td>
                    <td><?php echo htmlspecialchars($row['company_industry']); ?></td>
                    <td><?php echo format_currency($row['project_budget']); ?></td>
                    <td><?php echo htmlspecialchars($row['project_status']); ?></td>
                    <td><?php echo htmlspecialchars($row['task_title'] ?? 'No tasks'); ?></td>
                    <td><?php echo htmlspecialchars($row['task_status'] ?? '-'); ?></td>
                    <td><?php echo htmlspecialchars($row['contact_name'] ?? 'Unassigned'); ?></td>
                </tr>
            <?php endwhile; ?>
        </tbody>
    </table>
</body>
</html>
<?php
mysqli_close($conn);
?>
