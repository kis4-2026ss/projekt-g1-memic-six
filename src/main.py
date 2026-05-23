import argparse
import json
import os
import datetime
import subprocess
import time
from src.engine.migration_engine import MigrationEngine
from src.generator.csharp_generator import CSharpProjectGenerator
from src.validation.test_generator import TestGenerator
from src.validation.test_runner import TestRunner
from src.validation.comparator import Comparator

def main():
    parser = argparse.ArgumentParser(description="WebLegacy AI - PHP to C# Migration Tool")
    parser.add_argument("--php-files", type=str, nargs='+', help="Paths to one or more legacy PHP files or directories to migrate")
    parser.add_argument("--schema-sql", type=str, default=None, help="Path to database SQL schema file")
    parser.add_argument("--output-dir", type=str, default="./output", help="Directory to save generated C# code")
    parser.add_argument("--skip-validation", action="store_true", help="Skip running validation tests against the generated C# project and the original PHP code")
    
    args = parser.parse_args()

    if not args.php_files:
        print("Please provide at least one PHP file using --php-files")
        # For testing purposes, run a dummy migration if no file is provided
        print("Running a sample migration...")
        sample_php = """
        <?php
        $conn = new mysqli($servername, $username, $password, $dbname);
        $sql = "SELECT id, firstname, lastname FROM MyGuests";
        $result = $conn->query($sql);
        
        $guests = array();
        if ($result->num_rows > 0) {
            while($row = $result->fetch_assoc()) {
                $guests[] = $row;
            }
        }
        echo json_encode($guests);
        $conn->close();
        ?>
        """
        engine = MigrationEngine()
        result = engine.run_migration({"sample.php": sample_php})
        print("\n--- Migration Result ---")
        print(json.dumps(result, indent=2))
        return

    sql_schema = None
    if args.schema_sql:
        if os.path.exists(args.schema_sql) and os.path.isfile(args.schema_sql):
            with open(args.schema_sql, 'r', encoding='utf-8', errors='ignore') as f:
                sql_schema = f.read()
            print(f"Loaded target database schema from: {args.schema_sql}")
        else:
            print(f"Warning: SQL schema file not found or invalid: {args.schema_sql}")

    php_codes = {}
    for path in args.php_files:
        if not os.path.exists(path):
            print(f"Error: Path not found: {path}")
            return
            
        if os.path.isfile(path):
            if path.endswith('.php'):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    php_codes[path] = f.read()
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith('.php'):
                        full_path = os.path.join(root, file)
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            php_codes[full_path] = f.read()
                            
    if not php_codes:
        print("Error: No PHP files found in the provided paths.")
        return

    engine = MigrationEngine()
    result = engine.run_migration(php_codes, sql_schema=sql_schema)

    if args.output_dir == "./output":

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = os.path.join(args.output_dir, f"run_{timestamp}")
    else:
        run_output_dir = args.output_dir

    print(f"Generating C# project structure in {run_output_dir}...")
    generator = CSharpProjectGenerator(output_dir=run_output_dir)
    generator.write_generated_code(result)

    gen = result.get("generation", {})
    if not gen or "error" in gen:
        print("C# code generation failed. Aborting pipeline.")
        return

    print(f"Migration complete. Results saved in {run_output_dir}")

    if not args.skip_validation:
        print("\n--- Starting Validation Pipeline ---")
        import shutil
        
        if not shutil.which("php"):
            print("Error: 'php' executable not found in PATH. Cannot start PHP development server for validation.")
            return
            
        if not shutil.which("dotnet"):
            print("Error: 'dotnet' executable not found in PATH. Cannot start C# API for validation.")
            return

        php_dir = os.path.dirname(os.path.abspath(args.php_files[0])) if args.php_files else '.'
        
        print("Starting PHP Development Server...")
        php_process = subprocess.Popen(["php", "-S", "localhost:8000", "-t", php_dir])
        
        print("Building and Starting C# ASP.NET Core API...")
        csproj_path = os.path.join(run_output_dir, "GeneratedProject.csproj")
        csharp_process = subprocess.Popen(["dotnet", "run", "--project", csproj_path, "--urls", "http://localhost:5000"])
        
        print("Waiting for servers to start...")
        def wait_for_server(url, timeout=30):
            import urllib.request
            import urllib.error
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    urllib.request.urlopen(url, timeout=1)
                    return True
                except urllib.error.HTTPError:
                    return True  # HTTPError (e.g. 404) means the server is online and responding
                except Exception:
                    time.sleep(1)
            return False

        php_up = wait_for_server("http://localhost:8000", timeout=15)
        csharp_up = wait_for_server("http://localhost:5000", timeout=30)
        
        if not php_up or not csharp_up:
            print(f"Warning: One or more servers failed to start (PHP: {php_up}, C#: {csharp_up}). Validation may fail.")
        else:
            print("Both servers successfully online!")
        
        try:
            print("Generating test cases via Gemini...")
            tg = TestGenerator()
            combined_php = "\n".join(php_codes.values())
            test_cases = tg.generate_test_cases(combined_php, result.get("analysis", {}))
            
            if not test_cases:
                print("Failed to generate test cases. Aborting validation.")
            else:
                print(f"Generated {len(test_cases)} test cases. Running them now...")
                tr = TestRunner("http://localhost:8000", "http://localhost:5000")
                test_results = tr.run_tests(test_cases)
                
                print("Comparing outputs...")
                comp = Comparator()
                final_report = []
                for res in test_results:
                    php_res = res["php_result"]
                    cs_res = res["csharp_result"]
                    
                    print(f"Evaluating {res['test_case'].get('name')}...")
                    comp_result = comp.compare_outputs(php_res["body"], cs_res["body"], php_res["status"], cs_res["status"])
                    
                    final_report.append({
                        "test_case": res["test_case"].get("name", "Unnamed"),
                        "method": res["test_case"].get("method", "GET"),
                        "path": res["test_case"].get("path", "/"),
                        "match": comp_result.get("match", False),
                        "reason": comp_result.get("reason", ""),
                        "confidence": comp_result.get("confidence", 0.0),
                        "php_status": php_res["status"],
                        "csharp_status": cs_res["status"]
                    })
                    
                report_path = os.path.join(run_output_dir, "validation_report.json")
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(final_report, f, indent=2)
                    
                print(f"\nValidation complete! Report saved to {report_path}")
                
        finally:
            print("Shutting down background servers...")
            if os.name == 'nt':
                # Forcefully terminate the process trees on Windows to prevent orphaned background processes
                try:
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(php_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    php_process.terminate()
                try:
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(csharp_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    csharp_process.terminate()
            else:
                php_process.terminate()
                csharp_process.terminate()

if __name__ == "__main__":
    main()
