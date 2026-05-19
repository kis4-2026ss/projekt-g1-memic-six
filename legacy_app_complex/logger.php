<?php
// File-based logging system typical in older apps
function log_event($message, $level = 'INFO') {
    $logfile = __DIR__ . '/app_log.txt';
    $date = date('Y-m-d H:i:s');
    $ip = isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : 'Unknown';
    
    $log_entry = "[$date] [$level] [IP: $ip] $message\n";
    
    // Using old school fopen/fwrite
    $fp = fopen($logfile, 'a');
    if ($fp) {
        fwrite($fp, $log_entry);
        fclose($fp);
    }
}
?>
