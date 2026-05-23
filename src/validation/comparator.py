import os
import json
from src.utils.gemini_client import GeminiClient
from src.engine.prompts import MigrationPrompts

class Comparator:
    def __init__(self):
        self.gemini_client = GeminiClient()

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

        response_text = self.gemini_client.generate_content(prompt)

        # Clean up markdown JSON blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        try:
            result = json.loads(response_text.strip())
            return result
        except json.JSONDecodeError as e:
            print(f"Error parsing comparison result: {e}")
            return {
                "match": False,
                "reason": "Failed to parse Gemini comparison output.",
                "confidence": 0.0
            }
