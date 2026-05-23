import argparse
import json
import os
import datetime
from src.engine.migration_engine import MigrationEngine
from src.generator.csharp_generator import CSharpProjectGenerator

def main():
    parser = argparse.ArgumentParser(description="WebLegacy AI - PHP to C# Migration Tool")
    parser.add_argument("--php-files", type=str, nargs='+', help="Paths to one or more legacy PHP files or directories to migrate")
    parser.add_argument("--schema-sql", type=str, default=None, help="Path to database SQL schema file")
    parser.add_argument("--output-dir", type=str, default="./output", help="Directory to save generated C# code")
    
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

    print(f"Migration complete. Results saved in {run_output_dir}")

if __name__ == "__main__":
    main()
