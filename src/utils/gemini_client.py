import os
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY is not set in the environment.")
            self.client = None
        else:
            # Initialize the new Google GenAI client
            self.client = genai.Client(api_key=api_key)
        
        self.model_id = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-pro")

    def generate_content(self, prompt: str, response_schema=None) -> str:
        """
        Sends a prompt to the Gemini model and returns the response.
        Retries on rate limits (429 / RESOURCE_EXHAUSTED) with custom delay.
        """
        if not self.client:
            return '{"error": "GEMINI_API_KEY not configured."}'

        from google.genai import types
        import time

        config = None
        if response_schema:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            )

        max_retries = 3
        delay = 20  # Wait 20 seconds on 429 rate limit
        
        for attempt in range(max_retries + 1):
            try:
                # New SDK call syntax
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower() or "503" in error_msg or "500" in error_msg or "11001" in error_msg or "getaddrinfo" in error_msg
                
                if is_rate_limit and attempt < max_retries:
                    print(f"Rate limit exceeded (429). Retrying in {delay} seconds (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 1.5  # Increase delay slightly
                    continue
                
                print(f"Error calling Gemini API: {e}")
                return f"{{\"error\": \"{str(e)}\"}}"
