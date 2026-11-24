
"""
Idea Extraction Agent.
Converts any founder-submitted startup idea into structured information.
"""

import re
from typing import Optional

from base_agent import BaseAgent
from models import IdeaSubmission, StructuredIdea
from llm_client import UnifiedLLMClient


class IdeaExtractionAgent(BaseAgent):

    def __init__(self, llm_client: Optional[UnifiedLLMClient] = None):
        super().__init__(
            name="IdeaExtractionAgent",
            role="Structured Startup Idea Extraction",
            llm_client=llm_client
        )

    def run(self, submission: IdeaSubmission) -> StructuredIdea:

        self.log("Extracting structured startup parameters...")

        raw_idea = (submission.raw_idea or "").strip()

        if not raw_idea:
            raise ValueError(
                "Please enter a startup idea before validation."
            )

        industry_hint = (
            submission.domain_hint.strip()
            if submission.domain_hint else ""
        )

        geography = (
            submission.target_geography.strip()
            if submission.target_geography else "Global"
        )

        monetization = (
            submission.monetization_preference.strip()
            if submission.monetization_preference else ""
        )

        system_prompt = """
You are an expert startup incubator director and venture analyst.

Your task is to understand and structure ANY startup idea,
regardless of its industry.

IMPORTANT RULES:
- Analyze only the founder's current submission.
- Do not reuse information from previous startup ideas.
- Do not assume a particular industry or customer segment.
- Identify the actual problem and proposed solution.
- Identify the relevant industry from the submitted idea.
- Identify the actual people or organizations who would use or
  pay for the solution.
- Respect the optional industry hint and geography.
- Suggest a suitable monetization model if one is not provided.
- Do not invent features that are unrelated to the submission.
- Use clear and specific descriptions.
- Every field must describe the current startup idea.

Return ONLY valid JSON using this structure:

{
    "title": "Relevant startup name",
    "tagline": "One-line description",
    "problem_statement": "Actual problem",
    "solution_statement": "Proposed solution",
    "target_customer": "Relevant customers",
    "core_value_prop": "Main customer benefit",
    "industry_domain": "Relevant industry",
    "monetization_model": "Suitable revenue model",
    "key_keywords": [
        "keyword1",
        "keyword2",
        "keyword3",
        "keyword4",
        "keyword5"
    ]
}
"""

        user_prompt = f"""
CURRENT FOUNDER SUBMISSION:

Startup idea:
{raw_idea}

Industry hint:
{industry_hint or "Identify the industry from the idea"}

Target geography:
{geography}

Monetization preference:
{monetization or "Suggest a suitable model"}

Analyze this submission independently.
Do not use details from any previous startup.
Return the requested JSON.
"""

        data = {}

        try:
            data = self.execute_structured_prompt(
                system_prompt,
                user_prompt,
                temperature=0.2
            )

            if not isinstance(data, dict):
                data = {}

            if data.get("error") or data.get("raw_text"):
                data = {}

        except Exception as error:
            self.log(f"AI extraction failed: {error}")
            data = {}

        def get_value(field, fallback):
            value = data.get(field)

            if isinstance(value, str) and value.strip():
                return value.strip()

            return fallback

        # Create fallback keywords from the actual submission.
        words = re.findall(r"[A-Za-z0-9]+", raw_idea.lower())

        stop_words = {
            "the", "and", "for", "with", "that", "this",
            "from", "into", "using", "which", "their",
            "they", "them", "also", "will", "can", "its",
            "are", "is", "to", "of", "a", "an", "in", "on"
        }

        fallback_keywords = list(dict.fromkeys(
            word for word in words
            if len(word) > 3 and word not in stop_words
        ))[:5]

        if not fallback_keywords:
            fallback_keywords = ["startup idea", "customer problem"]

        keywords = data.get("key_keywords")

        if not isinstance(keywords, list) or not keywords:
            keywords = fallback_keywords

        keywords = [
            str(keyword).strip()
            for keyword in keywords
            if str(keyword).strip()
        ][:5]

        if not keywords:
            keywords = fallback_keywords

        # Build structured startup information.
        structured_idea = StructuredIdea(
            title=get_value(
                "title",
                "Startup Concept"
            ),

            tagline=get_value(
                "tagline",
                f"A solution addressing: {raw_idea[:150]}"
            ),

            problem_statement=get_value(
                "problem_statement",
                raw_idea
            ),

            solution_statement=get_value(
                "solution_statement",
                raw_idea
            ),

            target_customer=get_value(
                "target_customer",
                "Customers who experience the problem described "
                "in the founder's submission"
            ),

            core_value_prop=get_value(
                "core_value_prop",
                f"Addresses the customer problem: {raw_idea[:200]}"
            ),

            industry_domain=get_value(
                "industry_domain",
                industry_hint or "Industry to be identified"
            ),

            monetization_model=get_value(
                "monetization_model",
                monetization or
                "Suitable revenue model requires further evaluation"
            ),

            key_keywords=keywords
        )

        self.log(f"Final startup title: {structured_idea.title}")
        self.log(f"Final industry: {structured_idea.industry_domain}")
        self.log("Idea extraction completed.")

        return structured_idea
