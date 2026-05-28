import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import (
    MigrationPrompts,
    PHPAnalysisResult
)

class MigrationEngine:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def _extract_json(self, text: str) -> dict:
        text = text.strip()
        first_brace = text.find('{')
        first_bracket = text.find('[')
        
        start = -1
        end_char = ''
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            start = first_brace
            end_char = '}'
        elif first_bracket != -1:
            start = first_bracket
            end_char = ']'
            
        if start == -1:
            raise ValueError("No JSON structure found in response")
            
        end = text.rfind(end_char)
        if end == -1 or end < start:
            raise ValueError("Unterminated JSON structure in response")
            
        json_str = text[start:end+1]
        return json.loads(json_str)

    def analyze_php_code(self, php_codes: dict) -> dict:
        """
        Step 1: Analyze multiple PHP files and extract business intent.
        """
        combined_code = ""
        for filename, code in php_codes.items():
            combined_code += f"// --- File: {filename} ---\n{code}\n\n"
            
        prompt = MigrationPrompts.PHP_ANALYSIS_PROMPT.format(php_code=combined_code)
        response_text = self.gemini_client.generate_content(prompt, response_schema=PHPAnalysisResult)
        
        try:
            return self._extract_json(response_text)
        except Exception as e:
            print(f"Failed to parse JSON from Gemini analysis response: {e}")
            return {"error": "Invalid JSON response", "raw_response": response_text}

    def _extract_csharp_from_markdown(self, text: str) -> str:
        import re
        match = re.search(r'```csharp\s+(.*?)```', text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r'```\s+(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def generate_csharp_code(self, business_logic: dict, sql_schema: str = None) -> dict:
        """
        Step 2 & 3: Map to C# and generate code in stages.
        """
        if sql_schema:
            database_schema_context = f"Here is the target database SQL schema:\n```sql\n{sql_schema}\n```\n"
        else:
            database_schema_context = ""

        business_logic_str = json.dumps(business_logic, indent=2)
        
        components = [
            ("models_code", "Models", "All required Domain Entities and Data Transfer Objects (DTOs). Use data annotations. Place in the `GeneratedProject.Models` namespace."),
            ("context_code", "DbContext", "The `AppDbContext` class inheriting from `DbContext`, containing `DbSet<T>` for all entities. Place in the `GeneratedProject.Data` namespace. Include `using GeneratedProject.Models;`."),
            ("repository_code", "Repositories", "The Repository interfaces and their concrete implementations. Inject `AppDbContext` via constructor. Place in `GeneratedProject.Repositories`. Include `using GeneratedProject.Data;` and `using GeneratedProject.Models;`."),
            ("service_code", "Services", "The Service interfaces and implementations containing the core business logic. Inject repositories here. Do not access `AppDbContext` directly. Place in `GeneratedProject.Services`. Include `using GeneratedProject.Repositories;` and `using GeneratedProject.Models;`."),
            ("controller_code", "Controllers", "ASP.NET Core API Controllers inheriting from `ControllerBase`. Use `[ApiController]` and route attributes. Inject services. Place in `GeneratedProject.Controllers`. Include `using GeneratedProject.Services;` and `using GeneratedProject.Models;`.")
        ]
        
        result = {}
        previous_code = ""
        
        for key, name, description in components:
            print(f"Generating {name}...")
            prompt = MigrationPrompts.CSHARP_COMPONENT_PROMPT.format(
                database_schema_context=database_schema_context,
                business_logic_json=business_logic_str,
                component_name=name,
                component_description=description,
                previous_code_context=f"Previously generated context:\n{previous_code}" if previous_code else ""
            )
            
            response_text = self.gemini_client.generate_content(prompt)
            code = self._extract_csharp_from_markdown(response_text)
            result[key] = code
            
            # Append full generated code to context for next steps. Modern Gemini models have large input context windows.
            previous_code += f"// --- {name} Code ---\n"
            previous_code += code + "\n\n"
            
        return result

    def run_migration(self, php_codes: dict, sql_schema: str = None) -> dict:
        """
        Executes the full migration pipeline for given PHP files and optional SQL schema.
        """
        print("Starting analysis phase...")
        analysis_result = self.analyze_php_code(php_codes)
        
        if "error" in analysis_result and not "GEMINI_API_KEY not configured" in analysis_result.get("error", ""):
            print("Analysis failed. Aborting migration.")
            return {"analysis": analysis_result, "generation": None}
            
        print("Starting generation phase...")
        generation_result = self.generate_csharp_code(analysis_result, sql_schema)
        
        return {
            "analysis": analysis_result,
            "generation": generation_result
        }

