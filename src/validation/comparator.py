import os
import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import MigrationPrompts, ValidationComparisonResult

class Comparator:
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

    def compare_outputs(self, php_response: str, csharp_response: str, php_status: int, csharp_status: int) -> dict:
        if php_status != csharp_status:
            return {
                "match": False,
                "reason": f"Status code mismatch. PHP: {php_status}, C#: {csharp_status}",
                "confidence": 1.0
            }

        prompt = MigrationPrompts.VALIDATION_COMPARISON_PROMPT.format(
            php_output=php_response,
            csharp_output=csharp_response
        )

        response_text = self.gemini_client.generate_content(prompt, response_schema=ValidationComparisonResult)

        try:
            return self._extract_json(response_text)
        except Exception as e:
            print(f"Error parsing comparison result: {e}")
            return {
                "match": False,
                "reason": f"Failed to parse Gemini comparison output: {str(e)}",
                "confidence": 0.0
            }
