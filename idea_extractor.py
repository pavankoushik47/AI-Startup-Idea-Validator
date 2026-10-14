import os
import json
from dotenv import load_dotenv
from google import genai
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("API key missing. Check your .env file.")
else:
    client = genai.Client(api_key=api_key)
    startup_idea = input("Enter your startup idea: ")
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
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        if not response.text:
            print("Error: The AI returned an empty response.")
        else:
            idea_data = json.loads(response.text)
            print(json.dumps(idea_data, indent=4))
    except json.JSONDecodeError:
        print("Error: The AI returned invalid JSON.")
    except Exception as e:
        print("Error connecting to the AI:", e)

