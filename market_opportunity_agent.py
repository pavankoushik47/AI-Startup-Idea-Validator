import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


def analyze_market(idea_data):
    if not api_key:
        raise ValueError("API key missing. Check your .env file.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are a market opportunity and customer segmentation analyst.

    Analyze this startup idea:
    {json.dumps(idea_data, indent=2)}

    Return only valid JSON with these fields:
    1. market_opportunity
    2. industry_trends
    3. customer_segments

    Give useful, realistic analysis.
    Do not invent exact market-size statistics.
    If reliable data is unavailable, say so.
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )

    if not response.text:
        raise ValueError("The AI returned an empty response.")

    return json.loads(response.text)


if __name__ == "__main__":
    sample_idea = {
        "problem_statement": "College students struggle to find affordable meals.",
        "proposed_solution": "An app offering affordable meals near colleges.",
        "target_customers": "College students",
        "industry": "Food delivery",
        "key_features": [
            "Affordable meal listings",
            "Nearby restaurant discovery"
        ]
    }

    try:
        result = analyze_market(sample_idea)
        print(json.dumps(result, indent=4))
    except Exception as error:
        print("Error:", error)