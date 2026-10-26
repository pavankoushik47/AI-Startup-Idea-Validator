import os
import json
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
RETRY_DELAYS = [3, 8, 15]  # seconds to wait between retries


def _generate_with_retry(client, prompt):
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            return client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
        except Exception as e:
            temporary = any(c in str(e) for c in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED"))
            if not temporary or attempt == len(RETRY_DELAYS):
                raise
            print(f"Gemini is busy, retrying in {RETRY_DELAYS[attempt]}s...")
            time.sleep(RETRY_DELAYS[attempt])


def extract_idea(startup_idea):
    if not api_key:
        raise ValueError("API key missing. Check your .env file.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Analyze this startup idea and extract:
1. problem_statement
2. proposed_solution
3. target_customers
4. industry
5. key_features

Return only valid JSON with these five keys.

Startup idea: {startup_idea}
"""

    response = _generate_with_retry(client, prompt)
    if not response.text:
        raise ValueError("The AI returned an empty response.")
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("The AI returned invalid JSON.")


if __name__ == "__main__":
    startup_idea = input("Enter your startup idea: ")
    try:
        print(json.dumps(extract_idea(startup_idea), indent=4))
    except Exception as e:
        print("Error:", e)