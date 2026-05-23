<?php
// API Get Project Tree - Nested relations representation
header('Content-Type: application/json');
include('db.php');
include('functions.php');

$userId = isset($_GET['user_id']) ? intval($_GET['user_id']) : 1;

// 1. Fetch all projects
$projects_query = "
    SELECT p.id, p.name, p.budget, p.status, p.start_date, p.end_date, c.name AS company_name 
    FROM projects p
    INNER JOIN companies c ON p.company_id = c.id
    ORDER BY p.name ASC
";
$projects_res = mysqli_query($conn, $projects_query);

if (!$projects_res) {
    echo json_encode(["success" => false, "error" => mysqli_error($conn)]);
    exit;
}

$project_tree = [];

// 2. Fetch all tasks and map them by project
while ($project = mysqli_fetch_assoc($projects_res)) {
    $project_id = intval($project['id']);
    
    $tasks_query = "
        SELECT t.id, t.title, t.description, t.priority, t.status, t.estimated_hours, t.logged_hours, t.due_date,
               con.first_name, con.last_name, con.email
        FROM tasks t
        LEFT JOIN contacts con ON t.assigned_contact_id = con.id
        WHERE t.project_id = $project_id
        ORDER BY t.priority DESC, t.due_date ASC
    ";
    
    $tasks_res = mysqli_query($conn, $tasks_query);
    $tasks = [];
    
    if ($tasks_res) {
        while ($task = mysqli_fetch_assoc($tasks_res)) {
            $assigned_to = null;
            if ($task['email']) {
                $assigned_to = [
                    "name" => $task['first_name'] . " " . $task['last_name'],
                    "email" => $task['email']
                ];
            }
            
            $tasks[] = [
                "id" => intval($task['id']),
                "title" => $task['title'],
                "description" => $task['description'],
                "priority" => $task['priority'],
                "status" => $task['status'],
                "estimated_hours" => floatval($task['estimated_hours']),
                "logged_hours" => floatval($task['logged_hours']),
                "due_date" => $task['due_date'],
                "assigned_contact" => $assigned_to
            ];
        }
    }
    
    $project_tree[] = [
        "id" => $project_id,
        "name" => $project['name'],
        "company" => $project['company_name'],
        "budget" => floatval($project['budget']),
        "status" => $project['status'],
        "dates" => [
            "start" => $project['start_date'],
            "end" => $project['end_date']
        ],
        "tasks_count" => count($tasks),
        "tasks" => $tasks
    ];
}

// Track log
log_action($userId, 'GET_PROJECT_TREE', 'projects', NULL, 'Retrieved nested project and tasks hierarchy', $conn);

echo json_encode(["success" => true, "projects" => $project_tree]);

mysqli_close($conn);
?>
