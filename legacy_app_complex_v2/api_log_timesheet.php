<?php
// API Log Timesheet - Relational Checks & Transactions
header('Content-Type: application/json');
include('db.php');
include('functions.php');

$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    echo json_encode(["success" => false, "error" => "Invalid JSON input"]);
    exit;
}

$user_id = isset($data['user_id']) ? intval($data['user_id']) : 1;
$project_id = intval($data['project_id']);
$task_id = intval($data['task_id']);
$contact_id = intval($data['contact_id']);
$hours = floatval($data['hours_logged']);
$date = mysqli_real_escape_string($conn, $data['date_logged']);

if (empty($project_id) || empty($task_id) || empty($contact_id) || $hours <= 0 || empty($date)) {
    echo json_encode(["success" => false, "error" => "Missing required fields: project_id, task_id, contact_id, hours_logged, date_logged"]);
    exit;
}

// -------------------------------------------------------------------------
// START TRANSACTION
// -------------------------------------------------------------------------
mysqli_begin_transaction($conn);

try {
    // 1. Validate Project Status - Block completed projects
    $proj_query = "SELECT status, budget FROM projects WHERE id = $project_id FOR UPDATE";
    $proj_res = mysqli_query($conn, $proj_query);
    if (!$proj_res || mysqli_num_rows($proj_res) == 0) {
        throw new Exception("Project not found.");
    }
    
    $project = mysqli_fetch_assoc($proj_res);
    if ($project['status'] === 'completed') {
        throw new Exception("Forbidden: Cannot log hours to a completed project.");
    }
    
    // 2. Validate Task exists and belongs to the project
    $task_query = "SELECT id, logged_hours, estimated_hours FROM tasks WHERE id = $task_id AND project_id = $project_id FOR UPDATE";
    $task_res = mysqli_query($conn, $task_query);
    if (!$task_res || mysqli_num_rows($task_res) == 0) {
        throw new Exception("Task not found or does not belong to specified project.");
    }
    $task = mysqli_fetch_assoc($task_res);
    
    // 3. Insert Timesheet record
    $insert_ts = "
        INSERT INTO timesheets (project_id, task_id, contact_id, hours_logged, date_logged)
        VALUES ($project_id, $task_id, $contact_id, $hours, '$date')
    ";
    if (!mysqli_query($conn, $insert_ts)) {
        throw new Exception("Failed to insert timesheet: " . mysqli_error($conn));
    }
    $timesheet_id = mysqli_insert_id($conn);
    
    // 4. Update the Task's total logged hours
    $new_logged_hours = $task['logged_hours'] + $hours;
    $update_task = "
        UPDATE tasks 
        SET logged_hours = $new_logged_hours, status = 'in_progress' 
        WHERE id = $task_id
    ";
    if (!mysqli_query($conn, $update_task)) {
        throw new Exception("Failed to update task hours: " . mysqli_error($conn));
    }
    
    // 5. Track Action in Audit Logs
    log_action($user_id, 'LOG_HOURS', 'timesheets', $timesheet_id, "Logged $hours hours for contact $contact_id on task $task_id", $conn);
    
    // -------------------------------------------------------------------------
    // COMMIT TRANSACTION
    // -------------------------------------------------------------------------
    mysqli_commit($conn);
    
    echo json_encode([
        "success" => true,
        "timesheet_id" => $timesheet_id,
        "hours_logged" => $hours,
        "total_task_hours" => $new_logged_hours
    ]);
    
} catch (Exception $e) {
    // -------------------------------------------------------------------------
    // ROLLBACK TRANSACTION
    // -------------------------------------------------------------------------
    mysqli_rollback($conn);
    echo json_encode(["success" => false, "error" => $e->getMessage()]);
}

mysqli_close($conn);
?>
