import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not set in the environment.")
            self.client = None
        else:
            # Initialize the new Google GenAI client
            self.client = genai.Client(api_key=api_key)
        
        # Using the exact model ID from the list_models output
        self.model_id = 'gemini-flash-latest'

    def generate_content(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini model and returns the response.
        """
        if not self.client:
            return '{"error": "GEMINI_API_KEY not configured."}'

        try:
            # New SDK call syntax
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"{{\"error\": \"{str(e)}\"}}"
