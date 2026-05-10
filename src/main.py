import argparse
import json
import os
from src.engine.migration_engine import MigrationEngine

def main():
    parser = argparse.ArgumentParser(description="WebLegacy AI - PHP to C# Migration Tool")
    parser.add_argument("--php-files", type=str, nargs='+', help="Paths to one or more legacy PHP files to migrate")
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

    php_codes = {}
    for file_path in args.php_files:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return
        with open(file_path, 'r') as f:
            php_codes[file_path] = f.read()

    engine = MigrationEngine()
    result = engine.run_migration(php_codes)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Save the analysis result
    with open(os.path.join(args.output_dir, 'analysis.json'), 'w') as f:
        json.dump(result.get("analysis", {}), f, indent=2)

    # Save generated C# code pieces
    gen_result = result.get("generation", {})
    if isinstance(gen_result, dict):
        for key, code in gen_result.items():
            if key.endswith('_code') and code:
                filename = f"{key.replace('_code', '')}.cs"
                with open(os.path.join(args.output_dir, filename), 'w') as f:
                    f.write(code)
                print(f"Saved generated C# file: {filename}")

    print(f"Migration complete. Results saved in {args.output_dir}")

if __name__ == "__main__":
    main()
