import os
import json
from google import genai
from dotenv import load_dotenv
# Load the Gemini API key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Check your .env file."
    )
client = genai.Client(api_key=api_key)
def analyze_market(startup_idea):
    prompt = f"""
    Analyze the following startup idea for market opportunity
    and customer segmentation.
    Startup idea:
    {json.dumps(startup_idea, ensure_ascii=False)}
    Return a valid JSON object with these four fields:
    - market_opportunity
    - industry_trends
    - target_customer_segments
    - customer_needs
    Explain the opportunity, relevant trends, likely customer
    segments, and their needs.
    Do not invent exact market statistics. If reliable market
    data is unavailable, clearly state that.
    """
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )
    if not response.text:
        raise ValueError("The AI returned an empty response.")

    return json.loads(response.text)
if __name__ == "__main__":
    print("\n=== Market Opportunity Agent ===\n")
    problem = input(
        "1. What problem does your startup solve? "
    ).strip()
    solution = input(
        "2. What is your proposed solution? "
    ).strip()
    industry = input(
        "3. Which industry is it for? "
    ).strip()

    customers = input(
        "4. Who are your target customers? "
    ).strip()

    if not all([problem, solution, industry, customers]):
        print("\nPlease fill in all four details.")
    else:
        startup_idea = {
            "problem_statement": problem,
            "proposed_solution": solution,
            "industry": industry,
            "target_customers": customers
        }
        try:
            result = analyze_market(startup_idea)

            print("\n=== Market Analysis Report ===")
            print(json.dumps(result, indent=4, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Error: The AI returned invalid JSON.")
        except Exception as error:
            print("Error:", error)
