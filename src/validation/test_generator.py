import os
import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import MigrationPrompts

class TestGenerator:
    def __init__(self):
        self.gemini_client = GeminiClient()
        
    def generate_test_cases(self, php_code: str, analysis_json: dict) -> list:
        prompt = MigrationPrompts.VALIDATION_GENERATION_PROMPT.format(
            php_code=php_code,
            business_logic_json=json.dumps(analysis_json, indent=2)
        )
        
        response_text = self.gemini_client.generate_content(prompt)
        
        # Clean up markdown JSON blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            test_cases = json.loads(response_text.strip())
            return test_cases
        except json.JSONDecodeError as e:
            print(f"Error parsing generated test cases: {e}")
            print(f"Raw response: {response_text}")
            return []
