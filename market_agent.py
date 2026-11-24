
"""
Market Opportunity and Customer Segmentation Analysis Agent.
Works dynamically across different startup industries.
"""

import json
from typing import Optional

from base_agent import BaseAgent
from models import (
    StructuredIdea,
    WebSearchIntelligence,
    MarketOpportunity,
    CustomerPersona
)
from llm_client import UnifiedLLMClient


class MarketAnalysisAgent(BaseAgent):

    def __init__(self, llm_client: Optional[UnifiedLLMClient] = None):
        super().__init__(
            name="MarketAnalysisAgent",
            role="Market Opportunity & Customer Segmentation Analysis",
            llm_client=llm_client
        )

    def run(self, idea: StructuredIdea,
            search_data: WebSearchIntelligence) -> MarketOpportunity:

        self.log(f"Analyzing market opportunity for: {idea.title}")

        idea_data = (
            idea.model_dump() if hasattr(idea, "model_dump")
            else idea.dict()
        )

        search_data_dict = (
            search_data.model_dump() if hasattr(search_data, "model_dump")
            else search_data.dict()
        )

        # Reduce search data to control API token usage.
        compact_search_data = {
            "queries_executed": search_data_dict.get(
                "queries_executed", []
            )[:10],
            "market_signals_summary": str(
                search_data_dict.get("market_signals_summary", "")
            )[:1500],
            "real_world_stats": search_data_dict.get(
                "real_world_stats", []
            )[:5],
            "results": []
        }

        for item in search_data_dict.get("results", [])[:8]:
            if isinstance(item, dict):
                compact_search_data["results"].append({
                    "title": str(item.get("title", ""))[:150],
                    "source_domain": str(
                        item.get("source_domain", "")
                    )[:100],
                    "snippet": str(item.get("snippet", ""))[:500]
                })

        industry = str(
            idea_data.get("industry_domain") or "the specified industry"
        )

        problem = str(
            idea_data.get("problem_statement") or "the stated customer problem"
        )

        solution = str(
            idea_data.get("solution_statement") or "the proposed solution"
        )

        customers = str(
            idea_data.get("target_customer")
            or idea_data.get("target_customers")
            or "potential customers identified in the startup idea"
        )

        system_prompt = """
You are an experienced startup market research analyst.

Analyze ONLY the current startup idea supplied to you.

STRICT RULES:
- Do not reuse information from previous startup ideas.
- Do not assume a fixed industry or customer segment.
- Identify the actual industry, problem, solution, geography and customers.
- Every section must match the current startup idea.
- Use available web research as supporting evidence.
- Never invent market statistics, CAGR values, company names or surveys.
- If numerical evidence is missing, clearly explain what research is needed.
- Do not copy unrelated information from search results.
- Do not use competitors or market trends from a different industry.

MARKET SIZING:
- TAM: Total potential customers or organizations that could use
  this particular solution.
- SAM: The portion of that market the startup can realistically serve
  in its selected geography and customer segment.
- SOM: The realistic share the startup could obtain initially.
- Explain each estimate in the context of the supplied startup.
- Do not invent numerical market sizes.

CUSTOMER PERSONAS:
Create exactly TWO realistic customer personas.
Both must be relevant to the actual startup.
Include demographics, pain points, current workaround,
willingness to pay and buying trigger.
Clearly label willingness to pay as an estimate if unsupported.

MARKET DRIVERS AND BARRIERS:
Provide industry-specific drivers and barriers relevant to this idea.

Return ONLY valid JSON with this exact structure:

{
    "tam_estimate": "string",
    "sam_estimate": "string",
    "som_estimate": "string",
    "cagr_growth_rate": "string",
    "market_drivers": ["string"],
    "market_barriers": ["string"],
    "personas": [
        {
            "persona_name": "string",
            "target_demographics": "string",
            "core_pain_points": ["string"],
            "current_workaround": "string",
            "willingness_to_pay": "string",
            "key_buying_trigger": "string"
        }
    ],
    "market_timing_score": 70
}
"""

        user_prompt = f"""
CURRENT STARTUP IDEA:

Title: {idea_data.get("title", "")}
Industry: {industry}
Problem: {problem}
Solution: {solution}
Target customers: {customers}
Geography: {idea_data.get("geography", "Not specified")}

Complete idea details:
{json.dumps(idea_data, default=str)[:2500]}

CURRENT STARTUP'S WEB RESEARCH:
{json.dumps(compact_search_data, default=str)[:5000]}

Analyze ONLY this startup.
Make every market estimate, trend, barrier and persona relevant
to this startup's industry and customers.
Do not use information from another startup.
"""

        try:
            response = self.llm.generate(
                system_prompt,
                user_prompt,
                temperature=0.2,
                max_tokens=3000
            )

            data = self.llm.extract_json(response)

            if not isinstance(data, dict):
                raise ValueError("Invalid market analysis response.")

            for field in [
                "tam_estimate",
                "sam_estimate",
                "som_estimate",
                "cagr_growth_rate"
            ]:
                if not isinstance(data.get(field), str) or not data[field].strip():
                    data[field] = (
                        "Reliable numerical data is unavailable. "
                        "Further market research is required."
                    )

            for field in ["market_drivers", "market_barriers"]:
                if not isinstance(data.get(field), list):
                    data[field] = []

            # Convert AI-generated personas into model objects.
            personas = []
            raw_personas = data.get("personas", [])

            if isinstance(raw_personas, list):
                for persona in raw_personas[:2]:

                    if not isinstance(persona, dict):
                        continue

                    pain_points = persona.get("core_pain_points", [])

                    if not isinstance(pain_points, list):
                        pain_points = []

                    personas.append(
                        CustomerPersona(
                            persona_name=str(
                                persona.get("persona_name")
                                or "Potential Customer"
                            ),
                            target_demographics=str(
                                persona.get("target_demographics")
                                or customers
                            ),
                            core_pain_points=[
                                str(point) for point in pain_points
                            ],
                            current_workaround=str(
                                persona.get("current_workaround")
                                or "Existing methods used by the target customer"
                            ),
                            willingness_to_pay=str(
                                persona.get("willingness_to_pay")
                                or "Requires customer validation"
                            ),
                            key_buying_trigger=str(
                                persona.get("key_buying_trigger")
                                or "Need for the proposed solution"
                            )
                        )
                    )

            data["personas"] = personas

            try:
                score = int(data.get("market_timing_score", 70))
                data["market_timing_score"] = max(0, min(100, score))
            except (ValueError, TypeError):
                data["market_timing_score"] = 70

            result = MarketOpportunity(**data)

            self.log(
                f"Market analysis completed with {len(personas)} personas."
            )

            return result

        except Exception as e:

            self.log(f"Market analysis encountered an error: {e}")

            return MarketOpportunity(
                tam_estimate=(
                    f"The total potential market includes customers "
                    f"who experience this problem: {problem}. "
                    f"Exact market size requires reliable customer "
                    f"and industry data for {industry}."
                ),
                sam_estimate=(
                    f"The serviceable market consists of {customers} "
                    f"within the startup's selected geography who could "
                    f"use {solution}. Further research is required."
                ),
                som_estimate=(
                    "The obtainable market depends on initial customer "
                    "acquisition, partnerships and pilot adoption. "
                    "It must be validated."
                ),
                cagr_growth_rate=(
                    f"A reliable growth rate for this specific "
                    f"opportunity in {industry} could not be established "
                    f"from the available research."
                ),
                market_drivers=[
                    f"Growing demand for solutions addressing: {problem}",
                    f"Potential adoption of digital solutions in {industry}",
                    f"Customer interest in the benefits offered by {solution}"
                ],
                market_barriers=[
                    "Customer willingness to adopt a new solution requires validation",
                    "Customer acquisition and operational costs need assessment",
                    "The startup must validate its business model through pilot testing"
                ],
                personas=[],
                market_timing_score=70
            )
