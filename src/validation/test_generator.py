import os
import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import MigrationPrompts, ValidationTestSuite

class TestGenerator:
    def __init__(self):
        self.gemini_client = GeminiClient()
        
    def _extract_json(self, text: str) -> list:
        text = text.strip()
        first_bracket = text.find('[')
        first_brace = text.find('{')
        
        start = -1
        end_char = ''
        if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
            start = first_bracket
            end_char = ']'
        elif first_brace != -1:
            start = first_brace
            end_char = '}'
            
        if start == -1:
            raise ValueError("No JSON structure found in response")
            
        end = text.rfind(end_char)
        if end == -1 or end < start:
            raise ValueError("Unterminated JSON structure in response")
            
        json_str = text[start:end+1]
        return json.loads(json_str)

    def generate_test_cases(self, php_code: str, analysis_json: dict) -> list:
        prompt = MigrationPrompts.VALIDATION_GENERATION_PROMPT.format(
            php_code=php_code,
            business_logic_json=json.dumps(analysis_json, indent=2)
        )
        
        response_text = self.gemini_client.generate_content(prompt, response_schema=ValidationTestSuite)
        
        try:
            parsed = self._extract_json(response_text)
            if isinstance(parsed, dict) and "test_cases" in parsed:
                test_cases = parsed["test_cases"]
                if isinstance(test_cases, list):
                    return test_cases
            if isinstance(parsed, list):
                return parsed
            return []
        except Exception as e:
            print(f"Error parsing generated test cases: {e}")
            print(f"Raw response: {response_text}")
            return []
