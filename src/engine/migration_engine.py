import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import MigrationPrompts

class MigrationEngine:
    def __init__(self):
        self.gemini_client = GeminiClient()

    def analyze_php_code(self, php_codes: dict) -> dict:
        """
        Step 1: Analyze multiple PHP files and extract business intent.
        """
        combined_code = ""
        for filename, code in php_codes.items():
            combined_code += f"// --- File: {filename} ---\n{code}\n\n"
            
        prompt = MigrationPrompts.PHP_ANALYSIS_PROMPT.format(php_code=combined_code)
        response_text = self.gemini_client.generate_content(prompt)
        
        # Clean up the response to extract JSON (Gemini sometimes wraps it in markdown)
        try:
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("Failed to parse JSON from Gemini analysis response.")
            return {"error": "Invalid JSON response", "raw_response": response_text}

    def generate_csharp_code(self, business_logic: dict) -> dict:
        """
        Step 2 & 3: Map to C# and generate code.
        """
        business_logic_str = json.dumps(business_logic, indent=2)
        prompt = MigrationPrompts.CSHARP_GENERATION_PROMPT.format(business_logic_json=business_logic_str)
        response_text = self.gemini_client.generate_content(prompt)
        
        try:
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("Failed to parse JSON from Gemini generation response.")
            return {"error": "Invalid JSON response", "raw_response": response_text}

    def run_migration(self, php_codes: dict) -> dict:
        """
        Executes the full migration pipeline for given PHP files.
        """
        print("Starting analysis phase...")
        analysis_result = self.analyze_php_code(php_codes)
        
        if "error" in analysis_result and not "GEMINI_API_KEY not configured" in analysis_result.get("error", ""):
            print("Analysis failed. Aborting migration.")
            return {"analysis": analysis_result, "generation": None}
            
        print("Starting generation phase...")
        generation_result = self.generate_csharp_code(analysis_result)
        
        return {
            "analysis": analysis_result,
            "generation": generation_result
        }
